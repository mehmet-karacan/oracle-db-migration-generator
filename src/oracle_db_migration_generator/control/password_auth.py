"""Single local account, salted password hashes and revocable browser sessions."""
import hashlib
import hmac
import secrets
import time

COOKIE='odmg_session'
USERNAME='mkaracan'
DISPLAY_NAME='Mehmet KARACAN'


class PasswordAuth:
    def __init__(self,store):
        self.store=store
        with store.transaction() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS login_account(username TEXT PRIMARY KEY,salt BLOB,hash BLOB);
                CREATE TABLE IF NOT EXISTS login_sessions(token_hash TEXT PRIMARY KEY,expires REAL);
                CREATE TABLE IF NOT EXISTS login_attempts(bucket TEXT PRIMARY KEY,attempts INTEGER,until REAL);''')

    def setup_required(self):
        with self.store.transaction() as db:return not db.execute('SELECT 1 FROM login_account').fetchone()

    @staticmethod
    def password_hash(password,salt):
        return hashlib.scrypt(password.encode('utf-8'),salt=salt,n=32768,r=8,p=1,maxmem=64*1024*1024)

    def setup(self,password):
        if not isinstance(password,str) or not 12<=len(password)<=256:raise ValueError('PASSWORD_LENGTH_INVALID')
        salt=secrets.token_bytes(16);hashed=self.password_hash(password,salt)
        with self.store.transaction() as db:
            if db.execute('SELECT 1 FROM login_account').fetchone():raise FileExistsError('ACCOUNT_ALREADY_CONFIGURED')
            db.execute('INSERT INTO login_account VALUES(?,?,?)',(USERNAME,salt,hashed))

    def login(self,username,password,client):
        bucket=hashlib.sha256(client.encode()).hexdigest();clock=time.time()
        # One transaction also prevents parallel attempts bypassing the counter.
        with self.store.transaction() as db:
            prior=db.execute('SELECT attempts,until FROM login_attempts WHERE bucket=?',(bucket,)).fetchone()
            attempts=prior[0] if prior and prior[1]>clock else 0
            if attempts>=5:raise TimeoutError('LOGIN_RATE_LIMIT')
            account=db.execute('SELECT salt,hash FROM login_account WHERE username=?',(USERNAME,)).fetchone()
            valid=(isinstance(password,str) and len(password)<=256 and account is not None
                   and hmac.compare_digest(self.password_hash(password,account[0]),account[1]) and username==USERNAME)
            if not valid:
                db.execute('INSERT OR REPLACE INTO login_attempts VALUES(?,?,?)',(bucket,attempts+1,clock+900))
                token=None
            else:
                db.execute('DELETE FROM login_attempts WHERE bucket=?',(bucket,))
                db.execute('DELETE FROM login_sessions WHERE expires<=?',(clock,))
                token=secrets.token_urlsafe(32)
                db.execute('INSERT INTO login_sessions VALUES(?,?)',(self.token_hash(token),clock+8*3600))
        if token is None:raise PermissionError('LOGIN_INVALID')
        return token

    @staticmethod
    def token_hash(token):return hashlib.sha256(token.encode()).hexdigest()

    def identity(self,token):
        if not isinstance(token,str) or len(token)>128:raise PermissionError('IDENTITY_REQUIRED')
        with self.store.transaction() as db:
            row=db.execute('SELECT expires FROM login_sessions WHERE token_hash=?',(self.token_hash(token),)).fetchone()
        if not row or row[0]<=time.time():raise PermissionError('IDENTITY_REQUIRED')
        return {'user':USERNAME,'display_name':DISPLAY_NAME,'role':'shared','mode':'password'}

    def logout(self,token):
        if token:
            with self.store.transaction() as db:db.execute('DELETE FROM login_sessions WHERE token_hash=?',(self.token_hash(token),))
