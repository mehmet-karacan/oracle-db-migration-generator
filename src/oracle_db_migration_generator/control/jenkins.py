"""Server-configured job gateway. No credentials or source SQL in job parameters."""
from urllib.parse import urlsplit
import httpx


def dispatch(job_url,user,token,run_id):
    parsed=urlsplit(job_url)
    if (parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or not parsed.path.startswith('/job/')):
        raise ValueError('JENKINS_URL_INVALID')
    base=f'{parsed.scheme}://{parsed.netloc}'
    with httpx.Client(auth=(user,token),timeout=20,follow_redirects=False) as client:
        headers={};crumb=client.get(base+'/crumbIssuer/api/json')
        if crumb.status_code==200:
            data=crumb.json();field=data.get('crumbRequestField','')
            if field not in {'Jenkins-Crumb','.crumb'}:raise ValueError('JENKINS_CRUMB_INVALID')
            headers[field]=data['crumb']
        response=client.post(job_url.rstrip('/')+'/buildWithParameters',data={'RUN_ID':run_id},headers=headers)
        if response.status_code not in {201,302}:raise ValueError('JENKINS_DISPATCH_FAILED')
    return {'status':'QUEUED','executor':'JENKINS'}
