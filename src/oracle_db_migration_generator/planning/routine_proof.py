"""A separate, closed compiler-backed path. Exporter evidence is never fabricated."""
from dataclasses import dataclass, replace

from ..model.plan import DependencyReference
from ..model.serialization import digest, thaw
from ..parsing.dependencies import has_dynamic_sql
from ..oracle.routine_metadata import _base_snapshot, scoped_snapshot_matches, snapshot_binding_digest
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens


@dataclass(frozen=True)
class RoutineProof:
    references: tuple = ()
    evidence_ids: tuple = ()
    issues: tuple = ()

    @property
    def approved(self):
        return not self.issues


def _rows(record,field):
    value=record.get(field,{})
    if value.get('state')!='KNOWN':raise ValueError(field+' metadata erişimi doğrulanamadı')
    return value.get('rows',())


def _kind(kind):
    return {'PACKAGE':'PACKAGE_SPEC','TYPE':'TYPE_SPEC'}.get(kind,kind.replace(' ','_'))


def _metadata(snapshot):
    value=snapshot.capabilities.get('routine_metadata')
    if not value or value.state!='KNOWN':raise ValueError('ek bağımlılık metadata kaydı yok')
    data=value.value
    base=_base_snapshot(snapshot)
    if not (data.get('base_snapshot_digest')==base.semantic_digest
            and data.get('base_snapshot_binding')==snapshot_binding_digest(base)) and not scoped_snapshot_matches(base,data):
        raise ValueError('metadata farklı kaynak veya hedef bağlantı gözlemine ait')
    evidence={e.id:e for e in snapshot.evidence}
    if not value.evidence_ids or any(key not in evidence or evidence[key].side!=snapshot.side
            or evidence[key].query_id!='oracle.compiled-static/v1' or evidence[key].sha256!=digest(data)
            for key in value.evidence_ids):raise ValueError('metadata kanıt hash veya kökeni doğrulanamadı')
    records={}
    for item in data.get('records',()):
        key=(item.get('owner'),item.get('name'),item.get('kind'))
        if key in records:raise ValueError('yinelenen metadata kimliği')
        records[key]=item
    return data,records,value.evidence_ids


def _object(record,kind,*,optional=False):
    before=_rows(record,'before');after=_rows(record,'after')
    if before!=after:raise ValueError('toplama sırasında nesne durumu değişti')
    rows=[r for r in before if r[0]==kind]
    if optional and not before:return None
    if len(rows)!=1 or rows[0][1]!='VALID':raise ValueError(kind+' nesnesinin VALID durumu doğrulanamadı')
    return rows[0]


def _hash(record,field):
    value=record.get(field,{})
    if value.get('state')!='KNOWN' or not value.get('sha256'):raise ValueError(field+' tanım hash kanıtı yok')
    return value['sha256']


def compiled_static_inventory(context,obj):
    """Return None without a supplement, otherwise a proof or concrete holds.

    Fresh VALID + matching raw definition certifies only static binding. Target
    definitions, direct grants, namespace and dependency ordering remain gates.
    No compiler, DDL parse, function or user SQL is called here.
    """
    if 'routine_metadata' not in context.source.capabilities:return None
    evidence=();refs=[];issues=[]
    owner=obj.identity.owner.effective_name;name=obj.identity.name.effective_name
    kind={'PACKAGE_SPEC':'PACKAGE','PACKAGE_BODY':'PACKAGE BODY'}.get(obj.identity.object_type,obj.identity.object_type)
    try:
        if not context.source.source_origin or context.source.source_origin.get('kind')!='ORACLE':
            raise ValueError('kaynak derleyici kanıtı canlı Oracle kökenli değil')
        recorded_status=obj.properties.get('object_status')
        if not recorded_status or recorded_status.state!='KNOWN' or recorded_status.value!='VALID':
            raise ValueError('kayıtlı kaynak nesnenin VALID durumu doğrulanamadı')
        source,source_records,source_ids=_metadata(context.source)
        target,target_records,target_ids=_metadata(context.target);evidence=(*source_ids,*target_ids)
        if _rows(source,'identity')!=((owner,),) or _rows(target,'identity')!=((owner,),):
            raise ValueError('metadata oturum hesabı karşılaştırılan owner ile aynı değil')
        if source.get('oracle_version')!=target.get('oracle_version') or not source.get('oracle_version'):
            raise ValueError('kaynak ve hedef Oracle sürümü aynı değil')
        unit=source_records.get((owner,name,kind))
        if unit is None:raise ValueError('seçili birim için ek metadata toplanmadı')
        _object(unit,kind)
        if _hash(unit,'ddl')!=obj.ddl_sha256:raise ValueError('güncel kaynak tanımı kayıtlı DDL ile aynı değil')
        companion={'PACKAGE BODY':('PACKAGE','PACKAGE_SPEC'),
                   'TYPE BODY':('TYPE','TYPE_SPEC')}.get(kind)
        if companion:
            companion_kind,companion_type=companion
            desired_companion=context.lookup(owner,companion_type,name)
            source_companion=source_records.get((owner,name,companion_kind))
            if (desired_companion is None or source_companion is None
                    or _hash(source_companion,'ddl')!=desired_companion.ddl_sha256):
                raise ValueError('güncel kaynak tanım eşlikçisi snapshot ile aynı değil')
            _object(source_companion,companion_kind)
            actual_companion=context.lookup(owner,companion_type,name,desired=False)
            target_companion=target_records.get((owner,name,companion_kind))
            if target_companion is None:
                raise ValueError('hedef tanım eşlikçisi için metadata kaydı yok')
            companion_before=_rows(target_companion,'before')
            if companion_before!=_rows(target_companion,'after'):
                raise ValueError('toplama sırasında hedef tanım eşlikçisi değişti')
            if actual_companion is None:
                if companion_before:raise ValueError('hedef tanım eşlikçisi snapshot sonrasında oluşmuş')
            else:
                matching_companion=[row for row in companion_before if row[0]==companion_kind]
                if (len(matching_companion)!=1
                        or matching_companion[0][1] not in {'VALID','INVALID'}
                        or any(row[0] not in {companion_kind,kind} for row in companion_before)
                        or _hash(target_companion,'ddl')!=actual_companion.ddl_sha256):
                    raise ValueError('güncel hedef tanım eşlikçisi snapshot ile aynı değil')
        target_unit=target_records.get((owner,name,kind))
        if target_unit is None:raise ValueError('hedef birim için ek metadata toplanmadı')
        target_before=_rows(target_unit,'before')
        if target_before!=_rows(target_unit,'after'):
            raise ValueError('toplama sırasında hedef birim durumu değişti')
        target_root=context.lookup(owner,obj.identity.object_type,name,desired=False)
        if target_root is None:
            if target_before:raise ValueError('hedef birim snapshot sonrasında oluşmuş')
        else:
            allowed_kinds={'PACKAGE BODY':{'PACKAGE','PACKAGE BODY'},
                           'TYPE BODY':{'TYPE','TYPE BODY'}}.get(kind,{kind})
            matching_rows=[row for row in target_before if row[0]==kind]
            if (len(matching_rows)!=1
              or any(row[0] not in allowed_kinds for row in target_before)
              or matching_rows[0][1] not in {'VALID','INVALID'}
              or _hash(target_unit,'ddl')!=target_root.ddl_sha256):
                raise ValueError('güncel hedef birim tanımı snapshot ile aynı değil')
        if any(row[2]=='ERROR' for row in _rows(unit,'errors')):raise ValueError('kaynakta derleme hatası var')
        procedures=_rows(unit,'procedures')
        if not procedures or any(row[4]!='DEFINER' for row in procedures):raise ValueError('DEFINER çalışma bağlamı doğrulanamadı')
        settings=_rows(unit,'settings')
        if len(settings)!=1 or settings[0][0]!=kind or settings[0][6]:raise ValueError('koşullu derleme ayarları doğrulanamadı')
        tokens=code_tokens(obj.raw_ddl.decode()) or ();words={t.upper for t in tokens}
        if has_dynamic_sql(obj) or words & {'WRAPPED','JAVA','EXTERNAL','LIBRARY','CURRENT_USER'} or any(t.text.startswith('$') or t.text=='@' for t in tokens):
            raise ValueError('dinamik, uzak veya koşullu kod ayrı inceleme gerektiriyor')
        dependencies=_rows(unit,'dependencies')
        if dependencies!=_rows(unit,'dependencies_after'):
            raise ValueError('toplama sırasında derleyici bağımlılıkları değişti')
        if not dependencies:raise ValueError('boş derleyici envanteri tamlık kanıtı değil')
        captured=obj.properties.get('dictionary.dependencies')
        if captured and captured.state=='KNOWN':
            prior={(r['referenced_owner'],r['referenced_name'],r['referenced_type']) for r in captured.value}
            if prior!={(r[2],r[3],r[4]) for r in dependencies}:raise ValueError('kayıtlı ve güncel bağımlılık listesi değişti')
        for row in dependencies:
            if len(row)!=7 or row[0]!=name or row[1]!=kind or row[5] or row[6]!='HARD':
                raise ValueError('bağımlılık kimliği, uzak bağ veya HARD türü doğrulanamadı')
        def lookup(records,who,what,which):
            record=records.get((who,what,which)) or records.get((who,what,'RESOLVED'))
            if record is None:raise ValueError(who+'.'+what+' için metadata kaydı yok')
            _object(record,which)
            return record
        for row in dependencies:
            who,what,which=row[2:5]
            label=who+'.'+what
            try:
                if (who,what,which)==('SYS','SYS_STUB_FOR_PURITY_ANALYSIS','PACKAGE'):
                    # Oracle's compiler intrinsic is not an application EXECUTE
                    # grant. Prove it through the exact closed DBA dictionary query.
                    runtimes=[data.get('compiler_runtime',{}) for data in (source,target)]
                    if (any(runtime.get('objects',{}).get('state')!='KNOWN'
                            or runtime['objects'].get('rows')!=(('PACKAGE','VALID'),)
                            or not runtime.get('source_sha256') for runtime in runtimes)
                            or runtimes[0]['source_sha256']!=runtimes[1]['source_sha256']):
                        raise ValueError('Oracle derleyici paketinin iki ortamda eşdeğerliği doğrulanamadı')
                    continue
                src=lookup(source_records,who,what,which);dst=target_records.get((who,what,which)) or target_records.get((who,what,'RESOLVED'))
                if which=='SYNONYM':
                    if dst is None:raise ValueError('hedef synonym metadata kaydı yok')
                    _object(dst,'SYNONYM')
                    bindings=_rows(src,'synonym')
                    if len(bindings)!=1 or bindings!=_rows(dst,'synonym') or bindings[0][2]:
                        raise ValueError('synonym hedefi farklı, uzak veya belirsiz')
                    if who=='PUBLIC':
                        if _rows(src,'local_shadow') or _rows(dst,'local_shadow'):raise ValueError('PUBLIC synonym yerel nesneyle gölgeleniyor')
                    who,what=bindings[0][:2]
                    src=source_records.get((who,what,'RESOLVED'))
                    dst=target_records.get((who,what,'RESOLVED'))
                    if not src or not dst:raise ValueError('synonym gerçek hedefi okunamadı')
                    concrete=[r[0] for r in _rows(src,'before') if r[0] in {'TABLE','VIEW','PACKAGE','TYPE','SEQUENCE','PROCEDURE','FUNCTION'}]
                    if len(concrete)!=1:raise ValueError('synonym gerçek nesne türü belirsiz')
                    which=concrete[0];_object(src,which)
                if (who,what) in {('SYS','DBMS_SQL'),('SYS','DBMS_UTILITY'),('SYS','DBMS_PREPROCESSOR')}:
                    raise ValueError('çalışma zamanı SQL çalıştırabilen paket ayrı inceleme gerektiriyor')
                dep_kind=_kind(which)
                if dep_kind not in {'TABLE','VIEW','MATERIALIZED_VIEW','SEQUENCE','PACKAGE_SPEC','TYPE_SPEC','PROCEDURE','FUNCTION'}:
                    raise ValueError('bağımlılık nesne türü desteklenmiyor: '+which)
                if who==owner:
                    wanted=context.lookup(who,dep_kind,what);actual=context.lookup(who,dep_kind,what,desired=False)
                    if wanted is None or _hash(src,'dependency_ddl')!=wanted.ddl_sha256:
                        raise ValueError('güncel kaynak bağımlılık tanımı snapshot ile aynı değil')
                    if dst is None:raise ValueError('hedef bağımlılık metadata kaydı yok')
                    stamp=_object(dst,which,optional=True)
                    if actual is None:
                        if stamp is not None:raise ValueError('hedef envanteri snapshot sonrasında değişmiş')
                    else:
                        if stamp is None or _hash(dst,'dependency_ddl')!=actual.ddl_sha256:
                            raise ValueError('güncel hedef bağımlılık tanımı snapshot ile aynı değil')
                        if which in {'TABLE','VIEW'} and _rows(src,'columns')!=_rows(dst,'columns'):
                            raise ValueError('kaynak ve hedef kolon imzaları aynı değil')
                        if (which in {'PACKAGE','TYPE','PROCEDURE','FUNCTION'}
                                and wanted.ddl_sha256==actual.ddl_sha256
                                and (_rows(src,'arguments')!=_rows(dst,'arguments')
                                     or _rows(src,'procedures')!=_rows(dst,'procedures'))):
                            raise ValueError('yerel birimin etkin çağrı imzası aynı değil')
                    refs.append(DependencyReference(who,dep_kind,what,'SOURCE_DEPENDENCY'))
                else:
                    if dst is None:raise ValueError('hedef harici nesne metadata kaydı yok')
                    _object(dst,which)
                    if which in {'TABLE','VIEW'}:
                        if not _rows(src,'columns') or _rows(src,'columns')!=_rows(dst,'columns'):
                            raise ValueError('harici kolon imzaları aynı değil')
                    if which in {'VIEW','PACKAGE','TYPE','PROCEDURE','FUNCTION'} and _hash(src,'ddl')!=_hash(dst,'ddl'):
                        raise ValueError('harici nesne tanımları aynı değil')
                    if which in {'PACKAGE','TYPE','PROCEDURE','FUNCTION'} and (
                            _rows(src,'arguments')!=_rows(dst,'arguments')
                            or _rows(src,'procedures')!=_rows(dst,'procedures')):
                        raise ValueError('harici birimin etkin çağrı imzası aynı değil')
                    if which not in {'TABLE','VIEW','PACKAGE','TYPE','PROCEDURE','FUNCTION'}:
                        raise ValueError('harici nesne için tam imza desteği yok')
                    grants={r[1] for r in _rows(dst,'privileges') if r[0] in {owner,'PUBLIC'}}
                    required={'EXECUTE'} if which in {'PACKAGE','TYPE','PROCEDURE','FUNCTION'} else {'SELECT'}
                    if required=={'SELECT'} and 'READ' in grants:grants.add('SELECT')
                    # SYS.DUAL and SYS dictionary views are read-only Oracle
                    # facilities. An UPDATE elsewhere in the unit must not be
                    # misattributed to one of these static SELECT references.
                    oracle_read_only=(who=='SYS' and (which=='TABLE' and what=='DUAL'
                                      or which=='VIEW' and what.startswith(('ALL_','USER_'))))
                    if which in {'TABLE','VIEW'} and not oracle_read_only:
                        required.update(words & {'INSERT','UPDATE','DELETE'})
                    if not required<=grants:raise ValueError('doğrudan/PUBLIC yetki eksik: '+', '.join(sorted(required-grants)))
                    refs.append(DependencyReference(who,dep_kind,what,'COMPILED_EXTERNAL'))
            except (ValueError,KeyError,IndexError,TypeError) as error:
                issues.append(label+': '+str(error))
    except (ValueError,KeyError,IndexError,TypeError) as error:
        issues.append(owner+'.'+name+': '+str(error))
    return RoutineProof(tuple(sorted(set(refs),key=lambda r:(r.owner,r.object_type,r.name,r.role))),tuple(evidence),tuple(issues))
