from fastapi.testclient import TestClient
from oracle_db_migration_generator.control.api import create_app

PASSWORD='test-only-long-password-123'


def test_first_setup_login_cookie_logout_and_no_secret_storage(tmp_path):
    app=create_app(tmp_path,mode='password',local_execution=True,allow_password_setup=True,start_workers=False)
    with TestClient(app) as client:
        assert client.get('/api/auth/status').json()['setup_required'] is True
        assert client.get('/api/session').status_code==401
        assert client.post('/api/auth/setup',json={'password':'short'}).status_code==422
        setup=client.post('/api/auth/setup',json={'password':PASSWORD})
        assert setup.status_code==200
        assert client.post('/api/auth/setup',json={'password':PASSWORD}).status_code==409
        assert client.get('/api/session').status_code==401
        assert client.post('/api/auth/login',json={'username':'mkaracan','password':'wrong'}).status_code==401
        login=client.post('/api/auth/login',json={'username':'mkaracan','password':PASSWORD})
        assert login.status_code==200
        assert 'HttpOnly' in login.headers['set-cookie'] and 'SameSite=strict' in login.headers['set-cookie']
        who=client.get('/api/session').json()
        assert who['user']=='mkaracan' and who['display_name']=='Mehmet KARACAN' and who['role']=='shared'
        assert PASSWORD not in client.get('/api/projects').text
        token=client.cookies.get('odmg_session')
        assert token and token.encode() not in app.state.store.db.read_bytes()
        assert PASSWORD.encode() not in app.state.store.db.read_bytes()
        assert client.post('/api/auth/logout',json={}).status_code==200
        assert client.get('/api/session').status_code==401
        client.cookies.set('odmg_session',token)
        assert client.get('/api/session').status_code==401
        assert client.post('/api/auth/login',json={'username':'mkaracan','password':PASSWORD}).status_code==200
        with app.state.store.transaction() as db:db.execute('UPDATE login_sessions SET expires=0')
        assert client.get('/api/session').status_code==401


def test_login_rate_limit_origin_and_proxy_headers_cannot_bypass(tmp_path):
    app=create_app(tmp_path,mode='password',local_execution=True,allow_password_setup=True,start_workers=False)
    with TestClient(app) as client:
        assert client.post('/api/auth/setup',json={'password':PASSWORD},headers={'origin':'https://evil.test'}).status_code==403
        assert client.post('/api/auth/setup',json={'password':PASSWORD}).status_code==200
        assert client.get('/api/session',headers={'x-odmg-user':'mkaracan','x-odmg-role':'admin'}).status_code==401
        for _ in range(5):assert client.post('/api/auth/login',json={'username':'mkaracan','password':'wrong'}).status_code==401
        assert client.post('/api/auth/login',json={'username':'mkaracan','password':PASSWORD}).status_code==429


def test_network_service_cannot_bootstrap_even_behind_a_loopback_proxy(tmp_path):
    app=create_app(tmp_path,mode='password',start_workers=False)
    with TestClient(app,client=('127.0.0.1',1234)) as client:
        assert client.get('/api/auth/status').json()['setup_required'] is True
        assert client.post('/api/auth/setup',json={'password':PASSWORD}).status_code==403
