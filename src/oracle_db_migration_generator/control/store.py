"""Transactional control records, versioned secrets and immutable run specifications."""
from contextlib import contextmanager
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sqlite3
from uuid import uuid4,uuid5,NAMESPACE_URL

from cryptography.fernet import Fernet

from ..config.credentials import Credentials
from ..model.serialization import digest
from .models import ConnectionInput,ProfileInput,SettingsInput,ProjectInput,SchemaMappingInput,schema_scope

DEFAULT_PROJECT_ID=uuid5(NAMESPACE_URL,'urn:innova:generator:project:sky').hex


def now():return datetime.now(timezone.utc).isoformat()


class ControlStore:
    def __init__(self,root):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        key=self.root/'vault.key'
        if key.is_symlink():raise ValueError('VAULT_PATH_UNSAFE')
        external_key=os.environ.get('ODMG_UI_VAULT_KEY')
        if external_key:self.vault=Fernet(external_key.encode('ascii'))
        else:
            try:
                descriptor=os.open(key,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(descriptor,'wb') as stream:stream.write(Fernet.generate_key())
            except FileExistsError:pass
            self.vault=Fernet(key.read_bytes())
        self.db=self.root/'control.sqlite3'
        with self.transaction() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS records(kind TEXT,id TEXT,revision INTEGER,document TEXT,
                                PRIMARY KEY(kind,id,revision));
                CREATE TABLE IF NOT EXISTS secrets(id TEXT,revision INTEGER,token BLOB,PRIMARY KEY(id,revision));
                CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,document TEXT);
                CREATE TABLE IF NOT EXISTS comparison_views(run_id TEXT,target_id TEXT,sha256 TEXT,document TEXT,
                    PRIMARY KEY(run_id,target_id));
                CREATE TABLE IF NOT EXISTS scan_views(run_id TEXT,target_id TEXT,sha256 TEXT,document TEXT,PRIMARY KEY(run_id,target_id));
                CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,at TEXT,actor TEXT,action TEXT,record_id TEXT);''')
            db.execute('INSERT OR IGNORE INTO records VALUES(?,?,?,?)',('project',DEFAULT_PROJECT_ID,1,
                json.dumps({'id':DEFAULT_PROJECT_ID,'name':'SKY','code':'SKY','revision':1,'updated_at':now()})))

    @contextmanager
    def transaction(self):
        db=sqlite3.connect(self.db,timeout=15)
        try:
            db.execute('BEGIN IMMEDIATE');yield db;db.commit()
        except Exception:db.rollback();raise
        finally:db.close()

    def _record(self,db,kind,id):
        row=db.execute('SELECT document FROM records WHERE kind=? AND id=? ORDER BY revision DESC LIMIT 1',(kind,id)).fetchone()
        if row is None:raise KeyError('RECORD_NOT_FOUND')
        record=json.loads(row[0])
        if kind in {'connection','profile','schema_mapping'}:record.setdefault('project_id',DEFAULT_PROJECT_ID)
        return record

    def save_project(self,data,*,actor):
        values=self._input(data,ProjectInput)
        with self.transaction() as db:
            ids=[r[0] for r in db.execute("SELECT DISTINCT id FROM records WHERE kind='project'")]
            if any(self._record(db,'project',id)['code']==values['code'] and id!=data.get('id') for id in ids):
                raise ValueError('PROJECT_CODE_EXISTS')
            return self._save(db,'project',{**values,**{k:data[k] for k in ('id','revision') if k in data}},actor)

    def _project_scope(self,db,kind,data,values):
        prior=self._record(db,kind,data['id']) if data.get('id') else None
        project_id=values.get('project_id') or (prior['project_id'] if prior else DEFAULT_PROJECT_ID)
        self._record(db,'project',project_id)
        if prior and prior['project_id']!=project_id:raise ValueError('PROJECT_MEMBERSHIP_IMMUTABLE')
        values['project_id']=project_id
        return prior

    def _save(self,db,kind,data,actor):
        data=dict(data);id=data.get('id') or uuid4().hex
        previous=self._record(db,kind,id) if data.get('id') else None
        if previous and previous['revision']!=data.get('revision'):raise ValueError('REVISION_CONFLICT')
        data.update(id=id,revision=previous['revision']+1 if previous else 1,updated_at=now())
        db.execute('INSERT INTO records VALUES(?,?,?,?)',(kind,id,data['revision'],json.dumps(data)))
        db.execute('INSERT INTO audit(at,actor,action,record_id) VALUES(?,?,?,?)',(now(),actor,kind+'.save',id))
        return data

    @staticmethod
    def _input(data,model):
        return model.model_validate({k:v for k,v in data.items() if k not in {'id','revision','updated_at','credential_configured','capture_schemas','capture_summary'}}).model_dump()

    def save_connection(self,data,*,actor):
        values=self._input(data,ConnectionInput);username=values.pop('username');password=values.pop('password')
        with self.transaction() as db:
            prior=self._project_scope(db,'connection',data,values)
            if prior and prior['kind']!=values['kind']:raise ValueError('CONNECTION_KIND_IMMUTABLE')
            if values['kind']=='SNAPSHOT':
                captured=self._record(db,'capture',values['capture_id'])
                if captured['project_id']!=values['project_id']:raise ValueError('PROJECT_SCOPE_MISMATCH')
                if prior and prior['capture_id']!=values['capture_id']:raise ValueError('CAPTURE_IMMUTABLE')
                values.update(capture_schemas=captured['schemas'],capture_summary=captured['summary'])
            old=self._credentials(db,prior['id'],prior['revision']) if prior and prior['credential_configured'] else None
            user=username or (old.username if old else '')
            secret=password if password else (old.password if old else '')
            if values['kind']=='ORACLE' and (not user or not secret):raise ValueError('ORACLE_CREDENTIAL_REQUIRED')
            saved=self._save(db,'connection',{**values,**{k:data[k] for k in ('id','revision') if k in data},
                                               'credential_configured':bool(user and secret)},actor)
            if saved['credential_configured']:
                token=self.vault.encrypt(json.dumps({'username':user,'password':secret}).encode())
                db.execute('INSERT INTO secrets VALUES(?,?,?)',(saved['id'],saved['revision'],token))
            return saved

    def _credentials(self,db,id,revision):
        row=db.execute('SELECT token FROM secrets WHERE id=? AND revision=?',(id,revision)).fetchone()
        if not row:raise ValueError('CREDENTIALS_NOT_FOUND')
        values=json.loads(self.vault.decrypt(row[0]));return Credentials(values['username'],values['password'])

    def credentials(self,id,revision=None):
        with self.transaction() as db:
            return self._credentials(db,id,revision or self._record(db,'connection',id)['revision'])

    def connection(self,id,*,actor=None,role='admin'):
        with self.transaction() as db:record=self._record(db,'connection',id)
        if role not in {'admin','shared'} and actor not in record['allowed_users']:raise PermissionError('CONNECTION_FORBIDDEN')
        return record

    def list_records(self,kind,*,actor=None,role='admin',project_id=None):
        with self.transaction() as db:
            ids=[r[0] for r in db.execute('SELECT DISTINCT id FROM records WHERE kind=?',(kind,))]
            records=[self._record(db,kind,id) for id in ids]
        if kind=='connection' and role not in {'admin','shared'}:records=[r for r in records if actor in r['allowed_users']]
        if project_id is not None:records=[r for r in records if r.get('project_id')==project_id]
        return records

    def _scope_connections(self,db,values):
        source=self._record(db,'connection',values['source']['connection_id'])
        if source['kind']!=values['source']['kind']:raise ValueError('SOURCE_KIND_MISMATCH')
        if source['project_id']!=values['project_id']:raise ValueError('PROJECT_SCOPE_MISMATCH')
        for id in values['target_ids']:
            target=self._record(db,'connection',id)
            if target['kind'] not in {'ORACLE','SNAPSHOT'}:raise ValueError('TARGET_MUST_BE_ORACLE')
            if target['project_id']!=values['project_id']:raise ValueError('PROJECT_SCOPE_MISMATCH')
            if target['kind']=='SNAPSHOT':
                needed=[pair['target_schema'] for pair in (values.get('target_mappings') or {}).get(id,[])]
                if not set(needed or values['source']['schemas']).issubset(target['capture_schemas']):raise ValueError('CAPTURE_SCHEMA_NOT_EXPORTED')
        if source['kind']=='SNAPSHOT' and not set(values['source']['schemas']).issubset(source['capture_schemas']):raise ValueError('CAPTURE_SCHEMA_NOT_EXPORTED')

    def import_capture(self,data,*,name,project_id,actor):
        from ..portable.stream import read_capture
        import shutil
        capture=read_capture(data)
        # The existing mapping contract accepts unquoted schema names.
        import re
        if any(not re.fullmatch('[A-Z][A-Z0-9_$#]{0,127}',s) for s in capture.schemas):raise ValueError('CAPTURE_UI_SCHEMA_UNSUPPORTED')
        if not isinstance(name,str) or not 1<=len(name.strip())<=100:raise ValueError('CAPTURE_NAME_INVALID')
        id=uuid4().hex;folder=self.root/'captures'/id
        with self.transaction() as db:
            self._record(db,'project',project_id)
            folder.mkdir(parents=True,exist_ok=False)
            try:
                (folder/'capture.odmg.jsonl').write_bytes(data)
                summary={'sha256':capture.sha256,'captured_at':capture.header['captured_at'],'environment':capture.header['environment'],
                    'status':capture.status,'filter':capture.selection.to_dict(),
                    'inventory_complete':all(s.inventory_complete for s in capture.schemas.values()),
                    'selected_objects':sum(len(s.selected) for s in capture.schemas.values())}
                db.execute('INSERT INTO records VALUES(?,?,?,?)',('capture',id,1,json.dumps({'id':id,'project_id':project_id,
                    'sha256':capture.sha256,'schemas':list(capture.schemas),'summary':summary})))
                values=ConnectionInput(name=name,kind='SNAPSHOT',capture_id=id,project_id=project_id).model_dump()
                values.pop('username');values.pop('password')
                return self._save(db,'connection',{**values,'credential_configured':False,'capture_schemas':list(capture.schemas),'capture_summary':summary},actor)
            except Exception:
                shutil.rmtree(folder);raise

    def load_capture(self,connection):
        from ..portable.stream import read_capture,MAX_PACKET_BYTES
        import hashlib
        if connection['kind']!='SNAPSHOT':raise ValueError('CAPTURE_CONNECTION_REQUIRED')
        with self.transaction() as db:record=self._record(db,'capture',connection['capture_id'])
        if record['project_id']!=connection['project_id']:raise ValueError('PROJECT_SCOPE_MISMATCH')
        from ..model.snapshot_io import safe_path
        file=safe_path(self.root,'captures/'+record['id']+'/capture.odmg.jsonl')
        if file.is_symlink() or file.stat().st_size>MAX_PACKET_BYTES:raise ValueError('CAPTURE_INTEGRITY')
        data=file.read_bytes()
        if hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('CAPTURE_INTEGRITY')
        return read_capture(data)

    def save_schema_mapping(self,data,*,actor):
        values=self._input(data,SchemaMappingInput)
        with self.transaction() as db:
            self._project_scope(db,'schema_mapping',data,values)
            self._scope_connections(db,values)
            return self._save(db,'schema_mapping',{**values,**{k:data[k] for k in ('id','revision') if k in data}},actor)

    def save_profile(self,data,*,actor):
        values=self._input(data,ProfileInput)
        if values.get('capture_filter') is None:values.pop('capture_filter',None)
        with self.transaction() as db:
            self._project_scope(db,'profile',data,values)
            self._scope_connections(db,values)
            if values['mapping_id'] is not None:
                mapping=self._record(db,'schema_mapping',values['mapping_id'])
                if mapping['project_id']!=values['project_id']:raise ValueError('PROJECT_SCOPE_MISMATCH')
                if mapping['revision']!=values['mapping_revision']:raise ValueError('REVISION_CONFLICT')
                if schema_scope(values)!=schema_scope(mapping):raise ValueError('SCHEMA_MAPPING_SCOPE_MISMATCH')
            return self._save(db,'profile',{**values,**{k:data[k] for k in ('id','revision') if k in data}},actor)

    def settings(self,project_id=None):
        project_id=project_id or DEFAULT_PROJECT_ID
        id='defaults' if project_id==DEFAULT_PROJECT_ID else 'project-'+project_id
        with self.transaction() as db:
            self._record(db,'project',project_id)
            try:record=self._record(db,'settings',id)
            except KeyError:record={**SettingsInput().model_dump(),'id':id,'revision':0}
            return {**record,'project_id':project_id}

    def save_settings(self,data,*,actor,project_id=None):
        project_id=project_id or data.get('project_id') or DEFAULT_PROJECT_ID
        if data.get('project_id',project_id)!=project_id:raise ValueError('PROJECT_SCOPE_MISMATCH')
        values=self._input({k:v for k,v in data.items() if k!='project_id'},SettingsInput)
        id='defaults' if project_id==DEFAULT_PROJECT_ID else 'project-'+project_id
        with self.transaction() as db:
            self._record(db,'project',project_id)
            try:prior=self._record(db,'settings',id)
            except KeyError:prior=None
            if prior:return self._save(db,'settings',{**values,'project_id':project_id,'id':id,'revision':data.get('revision')},actor)
            if data.get('revision',0)!=0:raise ValueError('REVISION_CONFLICT')
            saved=self._save(db,'settings',{**values,'project_id':project_id},actor)
            db.execute("UPDATE records SET id=?,document=? WHERE kind='settings' AND id=?",
                       (id,json.dumps({**saved,'id':id}),saved['id']))
            return {**saved,'id':id}

    def run_spec(self,profile_id,*,actor,role):
        if role not in {'admin','operator','shared'}:raise PermissionError('RUN_FORBIDDEN')
        with self.transaction() as db:
            profile=self._record(db,'profile',profile_id);project=self._record(db,'project',profile['project_id'])
        ids={profile['source']['connection_id'],*profile['target_ids']}
        connections={id:self.connection(id,actor=actor,role=role) for id in ids}
        if any(c['project_id']!=project['id'] for c in connections.values()):raise ValueError('PROJECT_SCOPE_MISMATCH')
        return {'project':project,'profile':profile,'settings':self.settings(project['id']),'connections':connections}

    def create_run(self,profile_id,*,actor,role,spec=None,external=None,executor=None):
        spec=spec if spec is not None else self.run_spec(profile_id,actor=actor,role=role)
        run={'id':uuid4().hex,'executor':executor or ('JENKINS' if external else 'LOCAL'),'artifact_mode':'JENKINS' if external or executor=='JENKINS' else 'LOCAL_PRIVATE','actor':actor,'status':'AWAITING_JENKINS' if external else 'QUEUED',
             'stage':'JENKINS_HANDOFF' if external else 'QUEUED','created_at':now(),
             'started_at':None,'finished_at':None,'error_code':None,'spec':spec,'settings_fingerprint':digest(spec),
             'targets':[],'events':[],'project_id':spec['project']['id'],'project_name':spec['project']['name'],
             'profile_name':spec['profile']['name']}
        if external:run['external']=external
        with self.transaction() as db:
            db.execute('INSERT INTO runs VALUES(?,?)',(run['id'],json.dumps(run)))
            db.execute('INSERT INTO audit(at,actor,action,record_id) VALUES(?,?,?,?)',(now(),actor,'run.create',run['id']))
        return run

    def run(self,id):
        with self.transaction() as db:row=db.execute('SELECT document FROM runs WHERE id=?',(id,)).fetchone()
        if not row:raise KeyError('RUN_NOT_FOUND')
        return self._run_project(json.loads(row[0]))

    @staticmethod
    def _run_project(run):
        run.setdefault('project_id',run['spec']['profile'].get('project_id',DEFAULT_PROJECT_ID))
        run.setdefault('profile_name',run['spec']['profile']['name'])
        return run

    def runs(self,*,project_id=None):
        with self.transaction() as db:
            if project_id is None:rows=db.execute('SELECT document FROM runs ORDER BY rowid DESC LIMIT 200')
            else:rows=db.execute("SELECT document FROM runs WHERE COALESCE(json_extract(document,'$.project_id'),?)=? ORDER BY rowid DESC LIMIT 200",(DEFAULT_PROJECT_ID,project_id))
            return [self._run_project(json.loads(r[0])) for r in rows]

    def scheduler_runs(self):
        with self.transaction() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT document FROM runs WHERE json_extract(document,'$.status') IN ('QUEUED','RUNNING') AND COALESCE(json_extract(document,'$.executor'),'LOCAL')='LOCAL' ORDER BY rowid")]

    def reserve_next_run(self,limit):
        # Capacity and FIFO claim must share one write transaction across API processes.
        with self.transaction() as db:
            runs=[json.loads(r[0]) for r in db.execute("SELECT document FROM runs WHERE json_extract(document,'$.status') IN ('QUEUED','RUNNING') AND COALESCE(json_extract(document,'$.executor'),'LOCAL')='LOCAL' ORDER BY rowid")]
            if sum(r['status']=='RUNNING' or bool(r.get('claimed')) for r in runs)>=limit:return None
            active=[r for r in runs if r['status']=='RUNNING' or r.get('claimed')]
            def eligible(r):
                project=r.get('project_id',DEFAULT_PROJECT_ID)
                return sum(a.get('project_id',DEFAULT_PROJECT_ID)==project for a in active)<r['spec']['settings']['max_parallel_jobs']
            run=next((r for r in runs if r['status']=='QUEUED' and not r.get('claimed') and eligible(r)),None)
            if run is None:return None
            run.update(claimed=True,claimed_at=now())
            db.execute('UPDATE runs SET document=? WHERE id=?',(json.dumps(run),run['id']))
            return run

    def update_run(self,id,**changes):
        with self.transaction() as db:
            row=db.execute('SELECT document FROM runs WHERE id=?',(id,)).fetchone()
            if not row:raise KeyError('RUN_NOT_FOUND')
            run=json.loads(row[0]);run.update(changes)
            db.execute('UPDATE runs SET document=? WHERE id=?',(json.dumps(run),id))
        return run

    def link_external_run(self,id,**changes):
        """Claim one observed build and finalize one request in a single transaction."""
        external=changes['external']
        with self.transaction() as db:
            row=db.execute('SELECT document FROM runs WHERE id=?',(id,)).fetchone()
            if not row:raise KeyError('RUN_NOT_FOUND')
            run=json.loads(row[0]);previous=run.get('external',{})
            if previous.get('result_digest'):
                if previous['result_digest']!=external['result_digest']:raise ValueError('RESULT_ALREADY_LINKED')
                return run
            if run['status']!='AWAITING_JENKINS' or previous.get('mode')!='BROWSER_HANDOFF':
                raise ValueError('HANDOFF_NOT_PENDING')
            other=db.execute("SELECT id FROM runs WHERE id<>? AND json_extract(document,'$.external.job_url')=? AND json_extract(document,'$.external.build_number')=? LIMIT 1",
                             (id,external['job_url'],external['build_number'])).fetchone()
            if other:raise ValueError('JENKINS_BUILD_ALREADY_LINKED')
            run.update(changes)
            db.execute('UPDATE runs SET document=? WHERE id=?',(json.dumps(run),id))
            db.execute('INSERT INTO audit(at,actor,action,record_id) VALUES(?,?,?,?)',(now(),'shared','run.link_jenkins',id))
            return run

    def begin_run(self,id):
        with self.transaction() as db:
            row=db.execute('SELECT document FROM runs WHERE id=?',(id,)).fetchone()
            if not row:raise KeyError('RUN_NOT_FOUND')
            run=json.loads(row[0])
            if run['status']!='QUEUED':return False
            limit=run['spec']['settings']['max_parallel_jobs']
            others=[json.loads(row[0]) for row in db.execute("SELECT document FROM runs WHERE id<>? AND (json_extract(document,'$.status')='RUNNING' OR (json_extract(document,'$.status')='QUEUED' AND json_extract(document,'$.claimed')=1))",(id,))]
            if len(others)>=4 or sum(r.get('project_id',DEFAULT_PROJECT_ID)==run.get('project_id',DEFAULT_PROJECT_ID) for r in others)>=limit:return False
            run.update(status='RUNNING',stage='SOURCE',started_at=now(),pid=os.getpid())
            db.execute('UPDATE runs SET document=? WHERE id=?',(json.dumps(run),id))
        return True
