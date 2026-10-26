"""Closed BasicFiles storage proof for a new, nonpartitioned heap table."""
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, enclosed, identifier
from .table_ddl import source_projection


def _storage_parameters(tokens):
    at=0;seen=set()
    while at<len(tokens):
        key=tokens[at].upper;at+=1
        if key=='FREELIST':
            if at>=len(tokens) or tokens[at].upper!='GROUPS':return None
            key='FREELIST_GROUPS';at+=1
        if key in seen or at>=len(tokens):return None
        seen.add(key);value=tokens[at].upper;at+=1
        if key in {'INITIAL','NEXT','MINEXTENTS','MAXEXTENTS','FREELISTS','FREELIST_GROUPS'}:
            if not value.isdecimal() or int(value)<1:return None
        elif key=='PCTINCREASE':
            if not value.isdecimal():return None
        elif key=='BUFFER_POOL':
            if value not in {'DEFAULT','KEEP','RECYCLE'}:return None
        elif key in {'FLASH_CACHE','CELL_FLASH_CACHE'}:
            if value not in {'DEFAULT','KEEP','NONE'}:return None
        else:return None
    return seen if seen else None


def _lob_parameters(tokens):
    at=0;seen=set();storage=set();cache=False;no_logging=False
    while at<len(tokens):
        key=tokens[at].upper;at+=1
        category={'ENABLE':'ROW_STORAGE','DISABLE':'ROW_STORAGE','CACHE':'CACHE_MODE',
                  'NOCACHE':'CACHE_MODE','LOGGING':'LOGGING_MODE','NOLOGGING':'LOGGING_MODE'}.get(key,key)
        if category in seen:return False
        seen.add(category)
        if key=='TABLESPACE':
            if at>=len(tokens):return False
            identifier(tokens[at]);at+=1
        elif key in {'ENABLE','DISABLE'}:
            if [t.upper for t in tokens[at:at+3]]!=['STORAGE','IN','ROW']:return False
            at+=3
        elif key in {'CHUNK','PCTVERSION','FREEPOOLS'}:
            if at>=len(tokens) or not tokens[at].text.isdecimal():return False
            value=int(tokens[at].text);at+=1
            if key=='CHUNK' and not 1<=value<=32768:return False
            if key=='PCTVERSION' and not 0<=value<=100:return False
            if key=='FREEPOOLS' and value<1:return False
        elif key=='RETENTION':
            if at<len(tokens) and tokens[at].upper in {'NONE','AUTO','MIN','MAX'}:return False
        elif key=='STORAGE':
            if at>=len(tokens) or tokens[at].text!='(':return False
            body,at=enclosed(tokens,at);storage=_storage_parameters(body)
            if storage is None:return False
        elif key=='CACHE':
            cache=True
            if at<len(tokens) and tokens[at].upper=='READS':at+=1
        elif key=='NOLOGGING':no_logging=True
        elif key not in {'NOCACHE','LOGGING'}:return False
    return bool(seen) and not (
        {'RETENTION','PCTVERSION'}<=seen or cache and no_logging
        or 'FREEPOOLS' in seen and bool(storage&{'FREELISTS','FREELIST_GROUPS'}))


def verified_basicfile_lobs(context,obj,columns):
    projection=source_projection(obj)
    props=projection.properties.get('table_properties',{}) if projection else {}
    raw=props.get('lob_storage')
    version=context.target.capabilities.get('oracle_major')
    if (not raw or props.get('partitioning') or props.get('external') or props.get('cluster')
            or props.get('organization') or props.get('temporary')
            or not version or version.state!='KNOWN' or not isinstance(version.value,int) or version.value<11):
        return False
    tokens=code_tokens(raw) or ();at=0;seen=set()
    try:
        while at<len(tokens):
            if tokens[at].upper!='LOB' or tokens[at+1].text!='(':return False
            items,at=enclosed(tokens,at+1)
            names=[]
            for index,token in enumerate(items):
                if index%2:
                    if token.text!=',':return False
                else:names.append(identifier(token)[0])
            if not names or len(items)%2==0 or seen.intersection(names) or len(set(names))!=len(names):return False
            for name in names:
                field=columns.get(name,{}).get('data_type')
                if not field or field.state!='KNOWN' or field.value not in {'CLOB','BLOB','NCLOB'}:return False
            seen.update(names)
            if [t.upper for t in tokens[at:at+3]]!=['STORE','AS','BASICFILE']:return False
            at+=3
            # Named segments introduce an additional target namespace to prove.
            if at>=len(tokens) or tokens[at].text!='(':return False
            params,at=enclosed(tokens,at)
            if not _lob_parameters(params):return False
        return bool(seen)
    except (ValueError,TypeError,IndexError):
        return False
