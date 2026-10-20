from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens

RULE_VERSION = 'oracle-safe-ddl/1.0'


def unsupported_table_feature(obj,*,partition_verified=False):
    projection = getattr(obj,'projection',None)
    if projection:
        props = projection.properties.get('table_properties',{})
        if (props.get('partitioning') and not partition_verified) or props.get('lob_storage') or props.get('external') or props.get('cluster'):
            return True
        if props.get('organization') and 'INDEX' in props['organization'].upper():
            return True
    value = obj.properties.get('dictionary.tables')
    if value and value.state=='KNOWN':
        if any(row.get('partitioned')=='YES' and not partition_verified or row.get('iot_type') or row.get('cluster_name') for row in value.value):
            return True
    if obj.raw_ddl:
        words = [token.upper for token in code_tokens(obj.raw_ddl.decode()) or ()]
        if any(word in words for word in (('SUBPARTITION','LOB','EXTERNAL','CLUSTER') if partition_verified else ('PARTITION','SUBPARTITION','LOB','EXTERNAL','CLUSTER'))):
            return True
        if any(words[index:index+2]==['ORGANIZATION','INDEX'] for index in range(len(words)-1)):
            return True
    return False


def status_for(operations,complete):
    if not complete or any(op.decision=='BLOCKED' for op in operations):
        return 'BLOCKED'
    if any(op.decision=='REVIEW_REQUIRED' for op in operations):
        return 'REVIEW_REQUIRED'
    if any(op.decision=='READY' for op in operations):
        return 'READY'
    return 'NO_ACTION' if operations else 'NO_CHANGE'
