"""Prove explicit PK/UK index associations before creating an empty table key."""
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens,identifier
from .._vendor.analyzer_core.oracle.table import constraint_properties
from ..model.plan import DependencyReference
from ..parsing.statements import qualified_parts
from .table_ddl import source_projection


IMPLICIT_CONTINUATIONS=frozenset(('ENABLE DISABLE VALIDATE NOVALIDATE DEFERRABLE NOT INITIALLY RELY NORELY '
    'TABLESPACE PCTFREE INITRANS MAXTRANS STORAGE COMPRESS NOCOMPRESS LOGGING NOLOGGING LOCAL GLOBAL '
    'PARALLEL NOPARALLEL REVERSE NOREVERSE ONLINE').split())


def explicit_association(definition):
    association=constraint_properties(definition).get('index_association')
    tokens=code_tokens(association or '') or ()
    return tokens if len(tokens)>2 and tokens[2].upper not in IMPLICIT_CONTINUATIONS else ()


def _column_keys(raw_keys):
    result=[]
    for raw in raw_keys:
        tokens=code_tokens(raw) or ()
        if len(tokens)!=1: raise ValueError('BACKING_INDEX_EXPRESSION_UNSUPPORTED')
        result.append(identifier(tokens[0])[0])
    return tuple(result)


def existing_backing_index(context,index,table,columns):
    """Prove an implicit source key already has its complete target index.

    This preserves the existing index only; a different constraint name is
    still a separate reviewed difference. Explicit source index names and
    physical-storage requirements cannot be substituted by this rule.
    """
    if context.profile.policy.compare_physical_storage:return None
    actual=context.lookup(table.identity.owner.effective_name,'TABLE',table.identity.name.effective_name,desired=False)
    if actual is None or actual.coverage.ddl!='COMPLETE' or table.coverage.ddl!='COMPLETE':return None
    wanted=source_projection(table);observed=source_projection(actual);index_projection=source_projection(index)
    if wanted is None or observed is None or index_projection is None:return None
    required=('constraints','constraint_columns','indexes','index_columns')
    facts={name:actual.properties.get('dictionary.'+name) for name in required}
    if any(value is None or value.state!='KNOWN' for value in facts.values()):return None
    def matching_key(definition):
        details=constraint_properties(definition)
        keys=tuple(identifier(t)[0] for t in code_tokens(details.get('columns') or '') or () if t.text!=',')
        return details,keys
    source_keys=[]
    for name,definition in wanted.properties.get('constraints',{}).items():
        details,keys=matching_key(definition)
        if (name==index.identity.name.effective_name and keys==columns and details['kind'] in {'PRIMARY KEY','UNIQUE'}
                and details.get('enabled')!='DISABLE' and details.get('validation')!='NOVALIDATE'
                and details.get('deferrable')!='DEFERRABLE' and not explicit_association(definition)):
            source_keys.append('P' if details['kind']=='PRIMARY KEY' else 'U')
    if not source_keys:return None
    if any(direction not in {None,'ASC'} for direction in index_projection.properties.get('directions',())):return None
    visible=index_projection.properties.get('visibility') or 'VISIBLE'
    owner,name=table.identity.owner.effective_name,table.identity.name.effective_name
    for constraint in facts['constraints'].value:
        if (constraint.get('table_name')!=name or constraint.get('constraint_type') not in source_keys
                or constraint.get('status')!='ENABLED' or constraint.get('validated')!='VALIDATED'
                or constraint.get('deferrable')!='NOT DEFERRABLE' or constraint.get('deferred')!='IMMEDIATE'
                or constraint.get('index_owner')!=owner):continue
        key_columns=sorted((row for row in facts['constraint_columns'].value if row.get('constraint_name')==constraint['constraint_name']
                            and row.get('table_name')==name),key=lambda row:row.get('position',0))
        if tuple(row.get('column_name') for row in key_columns)!=columns:continue
        if [row.get('position') for row in key_columns]!=list(range(1,len(columns)+1)):continue
        if not any((detail['kind']=='PRIMARY KEY' if constraint['constraint_type']=='P' else detail['kind']=='UNIQUE')
                   and keys==columns and detail.get('enabled')!='DISABLE' and detail.get('validation')!='NOVALIDATE'
                   for detail,keys in (matching_key(definition) for definition in observed.properties.get('constraints',{}).values())):continue
        index_name=constraint.get('index_name')
        matches=[row for row in facts['indexes'].value if row.get('index_name')==index_name and row.get('table_name')==name
                 and row.get('table_owner')==owner and row.get('index_type')=='NORMAL' and row.get('uniqueness')=='UNIQUE'
                 and row.get('status')=='VALID' and row.get('partitioned')=='NO' and row.get('visibility')==visible]
        if len(matches)!=1:continue
        index_columns=sorted((row for row in facts['index_columns'].value if row.get('index_name')==index_name
                              and row.get('table_name')==name),key=lambda row:row.get('column_position',0))
        if tuple(row.get('column_name') for row in index_columns)!=columns or any(row.get('descend')!='ASC' for row in index_columns):continue
        if [row.get('column_position') for row in index_columns]!=list(range(1,len(columns)+1)):continue
        return tuple(sorted({ev for value in facts.values() for ev in value.evidence_ids}|set(actual.evidence_ids)))
    return None


def backing_reference(context,table,definition):
    """None means implicit index; a named association needs complete AST proof.

    Oracle permits USING INDEX with an existing named index. We emit that
    index separately before ADD CONSTRAINT, never synthesize or duplicate it.
    https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/managing-indexes.html
    """
    tokens=explicit_association(definition)
    if not tokens: return None
    finish=5 if len(tokens)>3 and tokens[3].text=='.' else 3
    names=qualified_parts(tokens[2:finish])
    owner=table.identity.owner.effective_name
    index_owner,index_name=(owner,names[0]) if len(names)==1 else names
    if index_owner!=owner: raise ValueError('BACKING_INDEX_OWNER_UNVERIFIED')
    obj=context.lookup(index_owner,'INDEX',index_name)
    if obj is None or obj.coverage.ddl!='COMPLETE':
        raise ValueError('BACKING_INDEX_SOURCE_UNVERIFIED')
    # A target index cannot already belong to a table proven absent there.
    # Contradictory observations are not repaired with an implicit new index.
    if context.lookup(index_owner,'INDEX',index_name,desired=False) is not None:
        raise ValueError('BACKING_INDEX_TARGET_CONFLICT')
    projection=source_projection(obj)
    if projection is None: raise ValueError('BACKING_INDEX_SOURCE_UNVERIFIED')
    props=projection.properties
    target=qualified_parts(code_tokens(props.get('target','')) or ())
    target_owner,target_name=(owner,target[0]) if len(target)==1 else target
    details=constraint_properties(definition)
    columns=_column_keys([token.text for token in code_tokens(details['columns'] or '') or () if token.text!=','])
    if (details['kind'] not in {'PRIMARY KEY','UNIQUE'} or details.get('enabled')=='DISABLE'
            or (target_owner,target_name)!=(owner,table.identity.name.effective_name)
            or props.get('kind')!='NORMAL' or props.get('availability','VALID')!='VALID'
            or _column_keys(props.get('keys',()))!=columns
            or any(direction not in {None,'ASC'} for direction in props.get('directions',()))
            or details.get('deferrable')=='DEFERRABLE' and props.get('unique')=='UNIQUE'):
        raise ValueError('BACKING_INDEX_ASSOCIATION_UNVERIFIED')
    return DependencyReference(index_owner,'INDEX',index_name,'BACKING_INDEX')
