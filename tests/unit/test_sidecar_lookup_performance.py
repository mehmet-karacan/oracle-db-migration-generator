from dataclasses import replace
import hashlib

from oracle_db_migration_generator.parsing.adapter import ParseResult
from oracle_db_migration_generator.source.models import SourceArtifact
from oracle_db_migration_generator.source.sidecars import merge_sidecars
from tests.factories import source


def artifacts(statements):
    text='';units=[]
    for statement in statements:
        units.append({'kind':'COMMENT','text':statement,'start_char':len(text),'end_char':len(text)+len(statement)})
        text+=statement+'\n'
    raw=text.encode();artifact=SourceArtifact('app/comments.sql','APP','COMMENT','COMMENT',raw,hashlib.sha256(raw).hexdigest())
    return artifact,{artifact.path:ParseResult((),tuple(units),(),'COMPLETE')}


def test_many_sidecars_do_not_rescan_every_parent_for_each_statement():
    snapshot=source(' '.join(f'CREATE TABLE APP.T{i}(ID NUMBER);' for i in range(80)))
    reads=[]
    class Counted:
        def __init__(self,obj):self.obj=obj
        @property
        def identity(self):reads.append(1);return self.obj.identity
        def __getattr__(self,key):return getattr(self.obj,key)
    snapshot=replace(snapshot,objects=tuple(Counted(obj) for obj in snapshot.objects))
    artifact,parsed=artifacts([f"COMMENT ON TABLE APP.T{i} IS 'Açıklama';" for i in range(80)])
    updated=merge_sidecars(snapshot,(artifact,),parsed_results=parsed)
    comments=[obj for obj in updated.objects if obj.identity.object_type=='COMMENT']
    assert len(comments)==80 and all(obj.identity.parent_key for obj in comments)
    assert len(reads)<80*12


def test_multibyte_sidecars_keep_exact_evidence_offsets_and_parent_ambiguity():
    snapshot=source('CREATE TABLE APP.T(ID NUMBER); CREATE VIEW APP.V AS SELECT ID FROM APP.T;')
    artifact,parsed=artifacts(["COMMENT ON TABLE APP.T IS 'İlk açıklama';","COMMENT ON COLUMN APP.T.ID IS 'İkinci';"])
    updated=merge_sidecars(snapshot,(artifact,),parsed_results=parsed)
    comments=[obj for obj in updated.objects if obj.identity.object_type=='COMMENT']
    assert len(comments)==2 and all(obj.coverage.ddl=='COMPLETE' for obj in comments)
    for obj in comments:
        ev=next(ev for ev in updated.evidence if ev.id==obj.evidence_ids[0])
        assert artifact.raw[ev.start_byte:ev.end_byte]==obj.raw_ddl
    table=next(obj for obj in snapshot.objects if obj.identity.object_type=='TABLE')
    view=next(obj for obj in snapshot.objects if obj.identity.object_type=='VIEW')
    duplicate=replace(view,identity=replace(view.identity,name=table.identity.name))
    ambiguous=merge_sidecars(replace(snapshot,objects=(table,duplicate)),(artifact,),parsed_results=parsed)
    assert all(obj.identity.parent_key is None and obj.coverage.ddl=='PARTIAL'
               for obj in ambiguous.objects if obj.identity.object_type=='COMMENT')
