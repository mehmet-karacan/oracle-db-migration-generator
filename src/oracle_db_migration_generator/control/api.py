"""Authenticated control API; deploy behind an identity-signing trusted proxy."""
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import re

from fastapi import Depends,FastAPI,HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse,JSONResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from ..model.snapshot_io import safe_path
from ..oracle.preflight import safe_error_code
from .auth import authenticate
from .store import ControlStore,DEFAULT_PROJECT_ID
from .password_auth import PasswordAuth,COOKIE
from .queue import LocalQueue
from .runner import isolated_connection_test


def create_app(root,*,mode='proxy',proxy_key='',start_workers=True,web_root=None,shared_workspace=True,local_execution=False,allow_password_setup=False):
    store=ControlStore(root);queue=LocalQueue(store)
    passwords=PasswordAuth(store) if mode=='password' else None
    local_runtime=mode=='local' or (mode=='password' and local_execution)
    @asynccontextmanager
    async def lifespan(app):
        if start_workers and local_runtime:queue.start()
        yield
        if start_workers and local_runtime:queue.close()
    app=FastAPI(title='SKY Schema Control',docs_url=None,redoc_url=None,lifespan=lifespan)
    app.state.store=store

    def check_origin(request):
        if request.method not in {'GET','HEAD','OPTIONS'}:
            origin=request.headers.get('origin')
            defaults='http://127.0.0.1:5173,http://localhost:5173' if mode=='local' else ''
            allowed={str(request.base_url).rstrip('/'),*os.environ.get('ODMG_UI_ALLOWED_ORIGINS',defaults).split(',')}
            if (origin and origin not in allowed) or request.headers.get('sec-fetch-site')=='cross-site':raise HTTPException(403,'ORIGIN_FORBIDDEN')
            try:size=int(request.headers.get('content-length','0'))
            except ValueError:raise HTTPException(400,'REQUEST_INVALID') from None
            limit=64*1024*1024 if request.url.path=='/api/captures/import' else 256*1024
            if size>limit:raise HTTPException(413,'REQUEST_TOO_LARGE')

    async def identity(request:Request):
        check_origin(request)
        try:
            who=passwords.identity(request.cookies.get(COOKIE)) if passwords else authenticate(request.headers,request.client.host if request.client else '',mode=mode,key=proxy_key)
        except PermissionError:raise HTTPException(401,'IDENTITY_REQUIRED') from None
        header=request.headers.get('x-odmg-project');query=request.query_params.get('project_id')
        if header and query and header!=query:raise HTTPException(422,'PROJECT_SCOPE_MISMATCH')
        project_id=header or query
        if project_id is None and request.method in {'POST','PUT'} and request.url.path!='/api/captures/import':
            try:body=await request.json()
            except ValueError:body={}
            if isinstance(body,dict):project_id=body.get('project_id')
        project_id=project_id or DEFAULT_PROJECT_ID
        if not re.fullmatch('[a-f0-9]{32}',project_id):raise HTTPException(422,'PROJECT_SCOPE_MISMATCH')
        if shared_workspace:who={**who,'user':who['user'] if passwords else 'shared','role':'shared'}
        return {**who,'project_id':project_id}

    def scoped_data(data,who):
        if data.get('project_id',who['project_id'])!=who['project_id']:raise HTTPException(422,'PROJECT_SCOPE_MISMATCH')
        return {**data,'project_id':who['project_id']}

    def scoped_record(record,who):
        if record.get('project_id',DEFAULT_PROJECT_ID)!=who['project_id']:raise HTTPException(404,'RECORD_NOT_FOUND')
        return record

    @app.get('/api/auth/status')
    def auth_status(request:Request):
        return JSONResponse({'password_login':bool(passwords),'setup_required':passwords.setup_required() if passwords else False,'setup_allowed':bool(allow_password_setup and request.client.host in {'127.0.0.1','::1','testclient'})},headers={'Cache-Control':'no-store'})

    @app.post('/api/auth/setup')
    def auth_setup(data:dict,request:Request):
        check_origin(request)
        if not passwords:raise HTTPException(404,'NOT_FOUND')
        if not allow_password_setup or request.client.host not in {'127.0.0.1','::1','testclient'}:raise HTTPException(403,'SETUP_LOOPBACK_ONLY')
        if set(data)!={'password'}:raise HTTPException(422,'CONFIGURATION_INVALID')
        try:passwords.setup(data['password'])
        except FileExistsError:raise HTTPException(409,'ACCOUNT_ALREADY_CONFIGURED') from None
        return JSONResponse({'configured':True},headers={'Cache-Control':'no-store'})

    @app.post('/api/auth/login')
    def auth_login(data:dict,request:Request):
        check_origin(request)
        if not passwords:raise HTTPException(404,'NOT_FOUND')
        if set(data)!={'username','password'}:raise HTTPException(422,'CONFIGURATION_INVALID')
        try:token=passwords.login(data['username'],data['password'],request.client.host)
        except TimeoutError:raise HTTPException(429,'LOGIN_RATE_LIMIT') from None
        except PermissionError:raise HTTPException(401,'LOGIN_INVALID') from None
        response=JSONResponse({'authenticated':True},headers={'Cache-Control':'no-store'})
        response.set_cookie(COOKIE,token,max_age=8*3600,httponly=True,samesite='strict',secure=not local_runtime or request.url.scheme=='https')
        return response

    @app.post('/api/auth/logout')
    def auth_logout(request:Request,who=Depends(identity)):
        if passwords:passwords.logout(request.cookies.get(COOKIE))
        response=JSONResponse({'authenticated':False},headers={'Cache-Control':'no-store'})
        response.delete_cookie(COOKIE,httponly=True,samesite='strict')
        return response

    def admin(who):
        if who['role'] not in {'admin','shared'}:raise HTTPException(403,'ADMIN_REQUIRED')

    def can_run(run,who):
        scoped_record(run,who)
        if who['role'] not in {'admin','shared'} and run['actor']!=who['user']:raise HTTPException(403,'RUN_FORBIDDEN')

    @app.exception_handler(ValidationError)
    @app.exception_handler(RequestValidationError)
    async def invalid(request,error):
        # Never echo Pydantic's input, which can contain a database password.
        return JSONResponse({'detail':'CONFIGURATION_INVALID'},status_code=422)

    @app.exception_handler(ValueError)
    async def bad_value(request,error):
        return JSONResponse({'detail':'REVISION_CONFLICT' if str(error)=='REVISION_CONFLICT' else 'CONFIGURATION_INVALID'},
                            status_code=409 if str(error)=='REVISION_CONFLICT' else 422)

    @app.exception_handler(KeyError)
    async def missing(request,error):return JSONResponse({'detail':'RECORD_NOT_FOUND'},status_code=404)

    @app.exception_handler(PermissionError)
    async def forbidden(request,error):return JSONResponse({'detail':'ACCESS_FORBIDDEN'},status_code=403)

    @app.get('/api/session')
    def session(who=Depends(identity)):
        return {**who,'read_only':True,'artifact_mode':'LOCAL_DEVELOPMENT' if local_runtime else 'JENKINS',
                'local_execution_available':local_runtime,'executor_configured':local_runtime or bool(os.environ.get('ODMG_UI_JENKINS_JOB_URL')),
                'schedule':{'time':'08:00','timezone':'Europe/Istanbul','managed_by':'JENKINS','editable':False}}

    @app.get('/api/connections')
    def connections(project_id:str|None=None,who=Depends(identity)):
        return store.list_records('connection',actor=who['user'],role=who['role'],project_id=who['project_id'])

    @app.get('/api/projects')
    def projects(who=Depends(identity)):return store.list_records('project')

    @app.post('/api/projects')
    def save_project(data:dict,who=Depends(identity)):
        admin(who);return store.save_project(data,actor=who['user'])

    @app.post('/api/connections')
    def save_connection(data:dict,who=Depends(identity)):
        admin(who);return store.save_connection(scoped_data(data,who),actor=who['user'])

    @app.post('/api/captures/package')
    def capture_package(data:dict,who=Depends(identity)):
        admin(who)
        from ..portable.builder import package_files
        import io,zipfile
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as package:
            for name,content in package_files(data).items():package.writestr(name,content.encode('utf-8'))
        return Response(buffer.getvalue(),media_type='application/zip',headers={'Cache-Control':'no-store','Content-Disposition':'attachment; filename="oracle-capture.zip"'})

    @app.post('/api/captures/import',status_code=201)
    async def capture_import(request:Request,name:str,who=Depends(identity)):
        admin(who)
        from ..portable.stream import MAX_PACKET_BYTES
        data=bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data)>MAX_PACKET_BYTES:raise HTTPException(413,'REQUEST_TOO_LARGE')
        from starlette.concurrency import run_in_threadpool
        try:result=await run_in_threadpool(store.import_capture,bytes(data),name=name,project_id=who['project_id'],actor=who['user'])
        except ValueError as error:
            code=str(error)
            raise HTTPException(422,code if re.fullmatch('CAPTURE_[A-Z_]+',code) else 'CAPTURE_INVALID') from None
        return JSONResponse(result,status_code=201,headers={'Cache-Control':'no-store'})

    @app.get('/api/connections/{id}/access-info')
    def access_info(id:str,revision:int,who=Depends(identity)):
        admin(who)
        connection=scoped_record(store.connection(id,actor=who['user'],role=who['role']),who)
        if revision!=connection['revision']:raise HTTPException(409,'REVISION_CONFLICT')
        username=store.credentials(id,revision).username if connection['credential_configured'] else None
        return JSONResponse({'username':username,'credential_configured':connection['credential_configured']},
                            headers={'Cache-Control':'no-store'})

    @app.post('/api/connections/{id}/test')
    def check_connection(id:str,data:dict,who=Depends(identity)):
        connection=scoped_record(store.connection(id,actor=who['user'],role=who['role']),who)
        schemas=data.get('schemas',[])
        if (set(data)-{'schemas'} or not isinstance(schemas,list) or len(schemas)>20
                or any(not isinstance(s,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_$#]{0,127}',s) for s in schemas)):
            raise HTTPException(422,'SCHEMA_SCOPE_INVALID')
        try:return isolated_connection_test(store,connection,schemas=schemas)
        except Exception as error:
            code=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z_]{1,100}',str(error)) else safe_error_code(error)
            return JSONResponse({'status':'FAILED','error_code':code,'metadata_verified':False},status_code=422)

    @app.get('/api/profiles')
    def profiles(project_id:str|None=None,who=Depends(identity)):
        result=[]
        for profile in store.list_records('profile',project_id=who['project_id']):
            try:
                for id in {profile['source']['connection_id'],*profile['target_ids']}:
                    store.connection(id,actor=who['user'],role=who['role'])
            except PermissionError:continue
            result.append(profile)
        return result

    @app.get('/api/schema-mappings')
    def schema_mappings(project_id:str|None=None,who=Depends(identity)):
        result=[]
        for mapping in store.list_records('schema_mapping',project_id=who['project_id']):
            try:
                for id in {mapping['source']['connection_id'],*mapping['target_ids']}:
                    store.connection(id,actor=who['user'],role=who['role'])
            except PermissionError:continue
            result.append(mapping)
        return result

    @app.post('/api/schema-mappings')
    def save_schema_mapping(data:dict,who=Depends(identity)):
        admin(who);return store.save_schema_mapping(scoped_data(data,who),actor=who['user'])

    @app.post('/api/profiles')
    def save_profile(data:dict,who=Depends(identity)):
        admin(who)
        if data.get('target_mappings') is None:raise HTTPException(422,'TARGET_SCHEMA_SCOPE_REQUIRED')
        return store.save_profile(scoped_data(data,who),actor=who['user'])

    @app.get('/api/settings')
    def settings(who=Depends(identity)):
        admin(who);return store.settings(who['project_id'])

    @app.put('/api/settings')
    def save_settings(data:dict,who=Depends(identity)):
        admin(who);return store.save_settings(scoped_data(data,who),actor=who['user'],project_id=who['project_id'])

    @app.get('/api/runs')
    def runs(project_id:str|None=None,who=Depends(identity)):
        return [{k:v for k,v in r.items() if k!='spec'} for r in store.runs(project_id=who['project_id']) if who['role'] in {'admin','shared'} or r['actor']==who['user']]

    @app.post('/api/runs',status_code=202)
    def start_run(data:dict,who=Depends(identity)):
        if 'profile_id' not in data or set(data)-{'profile_id','project_id','executor'}:raise HTTPException(422,'PROFILE_REQUIRED')
        with store.transaction() as db:scoped_record(store._record(db,'profile',data['profile_id']),who)
        spec=store.run_spec(data['profile_id'],actor=who['user'],role=who['role'])
        if data.get('project_id',spec['project']['id'])!=spec['project']['id']:raise HTTPException(422,'PROJECT_SCOPE_MISMATCH')
        requested=data.get('executor')
        if requested not in {None,'LOCAL','JENKINS'}:raise HTTPException(422,'EXECUTOR_INVALID')
        if requested=='LOCAL' and not local_runtime:raise HTTPException(403,'LOCAL_EXECUTOR_UNAVAILABLE')
        if requested!='LOCAL' and any(c['kind']=='SNAPSHOT' for c in spec['connections'].values()):raise HTTPException(422,'CAPTURE_REQUIRES_LOCAL_EXECUTOR')
        if requested!='LOCAL':
            from .jenkins_browser import approved_handoff
            try:external=approved_handoff(spec,root=store.root)
            except ValueError:raise HTTPException(409,'JENKINS_PROFILE_NOT_CONFIGURED') from None
            if external:
                run=store.create_run(data['profile_id'],actor=who['user'],role=who['role'],spec=spec,external=external,executor='JENKINS')
                return {k:v for k,v in run.items() if k!='spec'}
        local_run=local_runtime and requested!='JENKINS'
        if not local_run and not all(os.environ.get(k) for k in ('ODMG_UI_JENKINS_JOB_URL','ODMG_UI_JENKINS_USER','ODMG_UI_JENKINS_TOKEN')):
            raise HTTPException(503,'JENKINS_EXECUTOR_NOT_CONFIGURED')
        run=store.create_run(data['profile_id'],actor=who['user'],role=who['role'],spec=spec,executor='LOCAL' if local_run else 'JENKINS')
        if not local_run:
            from .jenkins import dispatch
            try:dispatch(os.environ['ODMG_UI_JENKINS_JOB_URL'],os.environ['ODMG_UI_JENKINS_USER'],os.environ['ODMG_UI_JENKINS_TOKEN'],run['id'])
            except Exception:
                store.update_run(run['id'],status='FAILED',stage='FAILED',error_code='JENKINS_DISPATCH_FAILED')
                raise HTTPException(502,'JENKINS_DISPATCH_FAILED') from None
        return {k:v for k,v in run.items() if k!='spec'}

    @app.get('/api/runs/{id}')
    def run(id:str,who=Depends(identity)):
        result=store.run(id);can_run(result,who);return result

    @app.get('/api/runs/{id}/summary')
    def summary(id:str,who=Depends(identity)):
        from .summary import run_summary
        result=store.run(id);can_run(result,who)
        return run_summary(store,result)

    @app.get('/api/runs/{id}/operations')
    def operations(id:str,target_id:str,page:int=1,size:int=25,search:str='',decision:str='',who=Depends(identity)):
        result=store.run(id);can_run(result,who)
        if target_id not in result['spec']['profile']['target_ids']:raise HTTPException(404,'TARGET_NOT_FOUND')
        if page<1 or size not in {25,50,100} or len(search)>200:raise HTTPException(422,'PAGINATION_INVALID')
        plan_path=store.root/'runs'/id/'targets'/target_id/'plan.json'
        if not plan_path.is_file():return {'rows':[],'total':None,'plan_available':False}
        plan=json.loads(plan_path.read_bytes());rows=plan['operations']
        if decision:rows=[r for r in rows if r['decision']==decision]
        if search:
            needle=search.casefold();rows=[r for r in rows if needle in (r['object']['owner']+'.'+r['object']['name']+' '+r['reason_tr']).casefold()]
        return {'rows':rows[(page-1)*size:page*size],'total':len(rows),'plan_available':True,
                'counts':plan['counts'],'source':plan['source'],'scope':plan['scope']}

    @app.get('/api/runs/{id}/artifacts/{path:path}')
    def artifact(id:str,path:str,who=Depends(identity)):
        result=store.run(id);can_run(result,who)
        if result.get('executor')=='JENKINS' or result.get('external'):raise HTTPException(404,'ARTIFACT_NOT_FOUND')
        if not (path in {'index.html','README.md','run.json','source-preparation-performance.json'} or path.startswith(('assets/','targets/'))):
            raise HTTPException(404,'ARTIFACT_NOT_FOUND')
        try:file=safe_path(store.root/'runs'/id,path)
        except ValueError:raise HTTPException(400,'ARTIFACT_PATH_INVALID') from None
        if not file.is_file() or file.stat().st_size>64*1024*1024:raise HTTPException(404,'ARTIFACT_NOT_FOUND')
        headers={'X-Content-Type-Options':'nosniff','Cache-Control':'no-store'}
        if file.suffix=='.html':headers['Content-Security-Policy']="sandbox; default-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'self' data:"
        if file.suffix=='.sql':return FileResponse(file,media_type='text/plain; charset=utf-8',headers=headers)
        return FileResponse(file,headers=headers)

    @app.get('/api/runs/{id}/results/objects')
    def result_objects(id:str,target_id:str,page:int=1,size:int=25,search:str='',object_type:str='',difference_kind:str='',who=Depends(identity)):
        from .models import OBJECT_TYPES
        from .results import load_view,object_page,target_record
        run=store.run(id);can_run(run,who)
        try:target_record(run,target_id)
        except KeyError:raise HTTPException(404,'TARGET_NOT_FOUND') from None
        if page<1 or size not in {25,50,100} or len(search)>200 or object_type not in {'',*OBJECT_TYPES} or difference_kind not in {'','MISSING','EXTRA','CHANGED','UNKNOWN','INFORMATIONAL'}:
            raise HTTPException(422,'PAGINATION_INVALID')
        view=load_view(store,run,target_id)
        if view is None:return {'available':False,'total':None,'rows':[]}
        return object_page(view,page=page,size=size,search=search,object_type=object_type,difference_kind=difference_kind)

    @app.get('/api/runs/{id}/results/objects/{key}')
    def result_object(id:str,key:str,target_id:str,section:str='all',page:int=1,size:int=50,operation_page:int=1,grouped:bool=False,operation_group:str='',who=Depends(identity)):
        from .results import load_view,object_detail,target_record
        run=store.run(id);can_run(run,who)
        try:target_record(run,target_id)
        except KeyError:raise HTTPException(404,'TARGET_NOT_FOUND') from None
        if (not re.fullmatch('[a-f0-9]{64}',key) or section not in {'all','columns','constraints','indexes','other'}
                or page<1 or size not in {25,50,100} or operation_page<1 or len(operation_group)>2048):raise HTTPException(422,'PAGINATION_INVALID')
        view=load_view(store,run,target_id)
        if view is None:raise HTTPException(404,'RESULT_VIEW_UNAVAILABLE')
        return object_detail(view,run,target_id,key,category=section,page=page,size=size,operation_page=operation_page,grouped=grouped,operation_group=operation_group)

    @app.get('/api/runs/{id}/results/objects/{key}/definitions')
    def result_definitions(id:str,key:str,target_id:str,who=Depends(identity)):
        from .results import load_view,target_record
        from .definitions import object_definitions
        run=store.run(id);can_run(run,who)
        try:target_record(run,target_id)
        except KeyError:raise HTTPException(404,'TARGET_NOT_FOUND') from None
        if not re.fullmatch('[a-f0-9]{64}',key):raise HTTPException(422,'OBJECT_KEY_INVALID')
        view=load_view(store,run,target_id)
        if view is None:raise HTTPException(404,'RESULT_VIEW_UNAVAILABLE')
        return JSONResponse(object_definitions(store,run,target_id,key,view),headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

    @app.get('/healthz')
    def health():return {'status':'ok'}

    if web_root and (Path(web_root)/'index.html').is_file():
        app.mount('/',StaticFiles(directory=web_root,html=True),name='web')
    return app
