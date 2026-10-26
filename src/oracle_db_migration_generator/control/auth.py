"""Signed reverse-proxy identity; explicit local preview never accepts LAN clients."""
import hashlib
import hmac
import re
import time


def signature(key,user,role,timestamp):
    return hmac.new(key.encode(),f'{user}\n{role}\n{timestamp}'.encode(),hashlib.sha256).hexdigest()


def authenticate(headers,client,*,mode,key):
    if mode=='local':
        if client not in {'127.0.0.1','::1','testclient'}:raise PermissionError('LOCAL_MODE_LOOPBACK_ONLY')
        return {'user':'local-admin','role':'admin','mode':'local'}
    user=headers.get('x-odmg-user','');role=headers.get('x-odmg-role','');stamp=headers.get('x-odmg-timestamp','')
    if (mode!='proxy' or len(key)<32 or not re.fullmatch(r'[A-Za-z0-9_.@-]{1,128}',user)
            or role not in {'admin','operator','viewer'} or not stamp.isdigit()
            or abs(time.time()-int(stamp))>60
            or not hmac.compare_digest(headers.get('x-odmg-signature',''),signature(key,user,role,stamp))):
        raise PermissionError('IDENTITY_REQUIRED')
    return {'user':user,'role':role,'mode':'proxy'}
