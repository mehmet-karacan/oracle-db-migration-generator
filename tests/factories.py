import hashlib
from dataclasses import replace
from pathlib import Path

from oracle_db_migration_generator.config.loader import load_source_profile
from oracle_db_migration_generator.model.evidence import Evidence
from oracle_db_migration_generator.model.snapshot import Coverage, KnownValue, SchemaSnapshot
from oracle_db_migration_generator.model.serialization import thaw
from oracle_db_migration_generator.parsing.adapter import parse_source
from oracle_db_migration_generator.source.models import SourceArtifact, SourceInput, SourceRevision

ROOT = Path(__file__).resolve().parents[1]


def profile():
    return load_source_profile(ROOT/'examples/source-profile.example.json')


def source(sql,selected_profile=None):
    selected_profile = selected_profile or profile()
    raw = sql.encode()
    artifact = SourceArtifact('app/fixture.sql','APP','DDL','TABLE',raw,hashlib.sha256(raw).hexdigest())
    return replace(parse_source(SourceInput(SourceRevision('a'*40,None),(artifact,),hashlib.sha256(raw).hexdigest()),selected_profile),synthetic=True)


def actual(sql='',selected_profile=None):
    selected_profile = selected_profile or profile()
    scope = Evidence('ev-target-scope','ABSENCE_SCOPE','TARGET',None,'b'*64,None,None,'synthetic.inventory','Tam sentetik hedef envanteri.')
    capabilities = {key:KnownValue('KNOWN',value,(scope.id,)) for key,value in {
        'oracle_version':'19.0.0.0.0','oracle_major':19,'max_varchar2_bytes':4000,
        'max_bytes_per_character':4,'grantees':['READER','PUBLIC'],
        'coverage.COMMENT':'COMPLETE','coverage.GRANT':'COMPLETE'}.items()}
    if not sql:
        return SchemaSnapshot('snapshot/1.0',True,'TARGET',selected_profile.id,('APP',),None,'DEMO-TEST',(),
                              Coverage('COMPLETE','COMPLETE','COMPLETE'),capabilities,(scope,),'OBSERVED_STABLE')
    snapshot = source(sql,selected_profile)
    renamed = {ev.id:('target-'+ev.id if ev.side=='SOURCE' else ev.id) for ev in snapshot.evidence}
    objects = []
    for obj in snapshot.objects:
        props = {key:KnownValue(value.state,thaw(value.value),tuple(renamed.get(item,item) for item in value.evidence_ids))
                 for key,value in obj.properties.items()}
        if obj.identity.object_type=='TABLE':
            for group in ('partition_keys','indexes','index_columns'):
                props['dictionary.'+group] = KnownValue('KNOWN',[],(scope.id,))
        objects.append(replace(obj,properties=props,evidence_ids=tuple(renamed[item] for item in obj.evidence_ids),
                               coverage=replace(obj.coverage,dictionary='COMPLETE')))
    evidence = tuple(replace(ev,side='TARGET',kind='TARGET_METADATA' if ev.kind=='SOURCE_SPAN' else ev.kind,
                             id='target-'+ev.id) if ev.side=='SOURCE' else ev for ev in snapshot.evidence)
    evidence = evidence+(scope,)
    return replace(snapshot,side='TARGET',source_commit=None,target_id='DEMO-TEST',objects=tuple(objects),
                   completeness=replace(snapshot.completeness,dictionary='COMPLETE'),capabilities=capabilities,
                   evidence=evidence,observed_consistency='OBSERVED_STABLE')
