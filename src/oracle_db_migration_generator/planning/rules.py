from .. import __version__
from ..model.plan import TargetPlan
from ..model.serialization import digest
from ..model.validity import report_only_invalid_ddl
from ..parsing.fingerprint import PARSER_VERSION, parser_artifact_sha256, generator_artifact_sha256
from .builder import operation
from .context import PlanningContext
from .object_rules import object_change
from .policy import RULE_VERSION, status_for
from .table_rules import create_table, change_table
import re


def plan_target(differences,context):
    if differences.source_fingerprint!=context.source.semantic_digest or differences.target_fingerprint!=context.target.semantic_digest:
        raise ValueError('DIFFERENCE_SNAPSHOT_MISMATCH')
    groups = {}
    for diff in differences.differences:
        groups.setdefault(diff.object_key,[]).append(diff)
    operations = []
    for key,changes in sorted(groups.items()):
        desired,actual = context.source_objects.get(key),context.target_objects.get(key)
        obj = desired or actual
        if desired is None and all(d.kind=='EXTRA' for d in changes):
            operations.append(operation(context,obj,changes,'PRESERVE','INFORMATIONAL','TARGET_ONLY_OBJECT_PRESERVED','Hedefe özgü nesne korunuyor; DROP üretilmez.'))
        elif (any(d.kind=='UNKNOWN' for d in changes) and (actual is None or desired is None)
              or obj.coverage.ddl!='COMPLETE'):
            operations.append(operation(context,obj,changes,'REVIEW','BLOCKED','OBJECT_METADATA_INCOMPLETE','Eksik metadata veya doğrulanmamış yokluk güvenli SQL üretimini engelliyor.'))
        elif desired is None:
            operations.append(operation(context,obj,changes,'REVIEW','BLOCKED','SOURCE_ABSENCE_UNVERIFIED','Kaynak yokluğu doğrulanamadı.'))
        elif desired.identity.name.effective_name.startswith(('BIN$','SYS_','ISEQ$$_')) and desired.identity.object_type!='INDEX':
            operations.append(operation(context,obj,changes,'REVIEW','BLOCKED','RESERVED_INTERNAL_OBJECT','Oracle iç nesnesi otomatik oluşturulmaz.'))
        elif desired.identity.object_type=='TABLE':
            operations.extend(create_table(context,desired,changes) if actual is None else change_table(context,desired,actual,changes))
        elif not desired.raw_ddl and desired.identity.object_type not in {'COMMENT','GRANT'}:
            operations.append(operation(context,obj,changes,'REVIEW','BLOCKED','SOURCE_DDL_UNAVAILABLE','Ham kaynak DDL ve kapsamı doğrulanamadı.'))
        else:
            operations.extend(object_change(context,desired,actual,changes))
    from .graph import bind_and_order
    operations = bind_and_order(operations,context)
    warnings=list(differences.diagnostics)
    for op in operations:
        if set(op.reason_codes)&{'PHYSICAL_STORAGE_PRESERVED','BACKING_INDEX_CREATED_BY_CONSTRAINT'}:
            warnings.append(op.reason_codes[0]+': '+op.identity.owner.effective_name+'.'+op.identity.name.effective_name+' · '+op.reason_tr)
    for obj in context.target.objects:
        status=obj.properties.get('object_status')
        if status and status.state=='KNOWN' and status.value=='INVALID':
            errors=obj.properties.get('dictionary.errors')
            codes=sorted({code for row in errors.value for code in re.findall(r'(?:ORA|PLS)-\d{4,5}',str(row.get('text','')))}) if errors and errors.state=='KNOWN' else []
            warnings.append('TARGET_INVALID_OBJECT: '+obj.identity.owner.effective_name+'.'+obj.identity.name.effective_name+
                            ' ['+obj.identity.object_type+']'+(' · '+','.join(codes) if codes else ''))
            if obj.object_key not in context.source_objects and report_only_invalid_ddl(obj):
                warnings.append('TARGET_INVALID_DDL_REPORTED: '+obj.identity.owner.effective_name+'.'+obj.identity.name.effective_name+
                                ' ['+obj.identity.object_type+'] · INVALID; DDL ayrıştırması doğrulanamadı: '+
                                ', '.join(sorted(obj.coverage.diagnostics))+'.')
    external=context.target.capabilities.get('reference_objects')
    if external and external.state=='KNOWN':
        for ref in external.value:
            if ref['status']=='INVALID':
                warnings.append('TARGET_INVALID_REFERENCE: '+ref['owner']+'.'+ref['name']+' ['+ref['object_type']+']')
    return TargetPlan(context.source.synthetic or context.target.synthetic,__version__+'+sha256.'+generator_artifact_sha256(),RULE_VERSION,
                      {'profile_id':context.profile.id,'commit_sha':context.source.source_commit,'ddl_digest':context.source.semantic_digest},
                      {'id':context.target.target_id,'name':context.target_name,'schemas':context.target.schemas},
                      context.target.semantic_digest,differences.scope,status_for(operations,differences.complete),tuple(operations),
                      differences.differences,context.evidence,
                      {'profile_sha256':digest(context.profile),'policy_sha256':digest(context.profile.policy),
                       'parser_version':PARSER_VERSION,'parser_artifact_sha256':context.parser_hash_override or parser_artifact_sha256(),
                       'canonicalizer_version':'oracle-tokens/1.0','schema_contract_version':'plan/1.0'},tuple(sorted(set(warnings))))
