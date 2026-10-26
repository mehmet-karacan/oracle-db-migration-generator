"""Launch the optional shared UI API. Production is closed without signed identity."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.local/ui-state')
    parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=8800)
    parser.add_argument('--local-preview',action='store_true')
    parser.add_argument('--password-login',action='store_true')
    args=parser.parse_args()
    if args.local_preview and args.host not in {'127.0.0.1','::1'}:parser.error('Yerel önizleme yalnız loopback üzerinde açılır.')
    if not args.local_preview and not args.password_login and len(os.environ.get('ODMG_UI_PROXY_KEY',''))<32:
        parser.error('Ortak kullanım için en az 32 karakter ODMG_UI_PROXY_KEY ve imzalı kimlik proxy gerekir.')
    if not args.local_preview and not os.environ.get('ODMG_UI_VAULT_KEY'):
        parser.error('Ortak kullanım için dış secret deposundan ODMG_UI_VAULT_KEY gerekir.')
    from oracle_db_migration_generator.control.api import create_app
    import uvicorn
    app=create_app(args.root,mode='password' if args.password_login or args.local_preview else 'proxy',local_execution=args.local_preview,allow_password_setup=args.local_preview,proxy_key=os.environ.get('ODMG_UI_PROXY_KEY',''),
                   web_root=Path(__file__).resolve().parents[1]/'web/dist')
    uvicorn.run(app,host=args.host,port=args.port,proxy_headers=False,access_log=False)


if __name__=='__main__':main()
