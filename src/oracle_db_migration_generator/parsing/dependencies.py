"""Conservative token references, supplemented by exporter dependency evidence."""
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens, identifier
from ..model.plan import DependencyReference

BUILTIN_TYPES=frozenset(('NUMBER VARCHAR2 VARCHAR CHAR NCHAR NVARCHAR2 RAW LONG BINARY_FLOAT BINARY_DOUBLE FLOAT DEC DECIMAL INTEGER INT SMALLINT REAL DOUBLE DATE TIMESTAMP INTERVAL BLOB CLOB NCLOB BFILE BOOLEAN UROWID ROWID PLS_INTEGER BINARY_INTEGER SIMPLE_INTEGER NATURAL NATURALN POSITIVE POSITIVEN SIGNTYPE STRING').split())


def _cte_ranges(tokens):
    """Recognize ordinary query factoring; never hide a schema-qualified name.

    An alias is visible after its defining query, within the enclosing query
    only. Unsupported recursive/self references remain conservative references.
    """
    stack=[];ends={};parents={}
    for i,token in enumerate(tokens):
        parents[i]=stack[-1] if stack else None
        if token.text=='(':stack.append(i)
        elif token.text==')' and stack:ends[stack.pop()]=i
    ranges=[]
    for i,token in enumerate(tokens):
        if token.upper!='WITH':continue
        scope_end=ends.get(parents[i],len(tokens))
        scope_end=next((j for j in range(i+1,scope_end) if tokens[j].text==';'),scope_end)
        at=i+1
        while at<scope_end:
            try:name=identifier(tokens[at])[0]
            except ValueError:break
            at+=1
            if at<len(tokens) and tokens[at].text=='(':at=ends.get(at,scope_end)+1
            if at+1>=scope_end or tokens[at].upper!='AS' or tokens[at+1].text!='(':break
            close=ends.get(at+1)
            if close is None or close>=scope_end:break
            ranges.append((name,close+1,scope_end))
            at=close+1
            if at>=scope_end or tokens[at].text!=',':break
            at+=1
    return ranges


def type_reference(raw,owner,declared=()):
    tokens=code_tokens(raw or '') or ()
    if not tokens or tokens[0].upper in BUILTIN_TYPES: return None
    try:
        anchor=next((i for i,t in enumerate(tokens) if t.upper in {'%TYPE','%ROWTYPE'}),None)
        if anchor is not None:
            parts=[identifier(tokens[i])[0] for i in range(0,anchor,2)]
            if any(tokens[i].text!='.' for i in range(1,anchor,2)) or anchor+1!=len(tokens):
                raise ValueError('ANCHORED_TYPE_UNVERIFIED')
            suffix=tokens[anchor].upper[1:]
            if suffix=='TYPE' and len(parts)==3:
                return DependencyReference(parts[0],'TABLE',parts[1],'ANCHORED_COLUMN_TYPE',(parts[2],))
            if suffix=='ROWTYPE' and len(parts)==2:
                return DependencyReference(parts[0],'TABLE',parts[1],'ANCHORED_ROWTYPE')
            parent=parts[0] if parts else ''
            proof=next((ref for ref in declared if ref['owner']==owner and ref['name']==parent
                        and ref['type'] in {'TABLE','VIEW','MATERIALIZED VIEW','MATERIALIZED_VIEW'}),None)
            if proof and suffix=='TYPE' and len(parts)==2:
                return DependencyReference(owner,proof['type'].replace(' ','_'),parent,'ANCHORED_COLUMN_TYPE',(parts[1],))
            if proof and suffix=='ROWTYPE' and len(parts)==1:
                return DependencyReference(owner,proof['type'].replace(' ','_'),parent,'ANCHORED_ROWTYPE')
            # A record field or local variable can also be an anchor. It is
            # never evidence for a schema/type named by its first two tokens.
            return DependencyReference(owner,'ANCHORED_REFERENCE','.'.join(parts),'ANCHORED_REFERENCE_UNRESOLVED')
        first=identifier(tokens[0])[0]
        if len(tokens)>2 and tokens[1].text=='.':
            return DependencyReference(first,'TYPE_SPEC',identifier(tokens[2])[0],'USER_DEFINED_TYPE')
        return DependencyReference(owner,'TYPE_SPEC',first,'USER_DEFINED_TYPE')
    except ValueError: return None


def signature_only_spec(obj,projection):
    """A complete builtin-only interface cannot depend on body SQL tables.

    Exporters can group PACKAGE and PACKAGE BODY dictionary edges in one
    sidecar. Only this fully bounded interface can discard those coarse edges;
    declarations, defaults and custom types still require the full inventory.
    """
    if obj.identity.object_type!='PACKAGE_SPEC' or projection is None:return False
    props=projection.properties
    if props.get('initialization') or any(props.get('declarations',{}).values()):return False
    for routine in props.get('routines',()):
        if routine.call_references or routine.sql_statements:return False
        types=[parameter.data_type for parameter in routine.parameters]
        if any(parameter.default is not None for parameter in routine.parameters):return False
        if routine.return_type:types.append(routine.return_type)
        for datatype in types:
            tokens=code_tokens(datatype) or ()
            if not tokens or tokens[0].upper not in BUILTIN_TYPES or any(t.text in {'.','%'} for t in tokens):return False
    return True


def has_dynamic_sql(obj):
    tokens=code_tokens(obj.raw_ddl.decode()) if obj.raw_ddl else ()
    for i,token in enumerate(tokens):
        if token.upper=='EXECUTE' and i+1<len(tokens) and tokens[i+1].upper=='IMMEDIATE':return True
        if i+1<len(tokens) and tokens[i+1].text=='.':
            try:
                if identifier(token)[0]=='DBMS_SQL':return True
            except ValueError:pass
        if token.upper=='OPEN':
            end=next((j for j in range(i+1,len(tokens)) if tokens[j].text==';'),len(tokens))
            at=next((j for j in range(i+1,end) if tokens[j].upper=='FOR'),None)
            if at is not None and (at+1>=end or tokens[at+1].upper not in {'SELECT','WITH'}):return True
    return False


def _callee_parts(raw):
    """Only the qualified callee is an identifier; arguments are expressions."""
    tokens=code_tokens(raw or '') or ()
    if tokens and tokens[0].upper=='CALL':tokens=tokens[1:]
    result=[];at=0
    while at<len(tokens):
        if tokens[at].text in {'(',')',';',','}:break
        result.append(identifier(tokens[at])[0]);at+=1
        if at>=len(tokens) or tokens[at].text!='.':break
        at+=1
    return tuple(result)


def references(obj):
    refs=[];default=obj.identity.owner.effective_name
    declared=obj.properties.get('dependencies')
    declared_refs=declared.value if declared and declared.state=='KNOWN' else ()
    from ..compare.projection_adapter import restore_projection
    projection=restore_projection(obj)
    if obj.identity.object_type=='TABLE':
        for column in (projection.properties.get('columns',{}) if projection else {}).values():
            ref=type_reference(column.get('data_type'),default)
            if ref: refs.append(ref)
    if obj.identity.object_type=='TYPE_SPEC' and obj.raw_ddl:
        from .._vendor.analyzer_core.oracle.ddl_tokens import enclosed,top_level_items,source_span
        type_sql=obj.raw_ddl.decode()
        if projection and projection.properties.get('_generator_effective_create'):
            from .projections import normalize_projection
            if not normalize_projection(projection,type_sql).diagnostics:
                type_sql=projection.properties['_generator_effective_create']
        typed=code_tokens(type_sql) or ()
        words=[token.upper for token in typed]
        if 'OBJECT' in words:
            at=words.index('OBJECT')+1
            if at<len(typed) and typed[at].text=='(':
                body=enclosed(typed,at)
                for item in top_level_items(body[0]) if body else ():
                    if len(item)>1:
                        ref=type_reference(source_span(type_sql,item[1:]),default)
                        if ref: refs.append(ref)
        elif 'OF' in words:
            at=words.index('OF')+1
            ref=type_reference(source_span(type_sql,typed[at:]),default)
            if ref: refs.append(ref)
    if projection:
        analyses=projection.properties.get('_generator_routine_analysis',())
        if obj.identity.object_type in {'PACKAGE_SPEC','PACKAGE_BODY'}:
            analyses=[{'name':routine.name,'types':[p.data_type for p in routine.parameters]+([routine.return_type] if routine.return_type else []),
                       'calls':routine.call_references} for routine in projection.properties.get('routines',())]
        package=obj.identity.object_type in {'PACKAGE_SPEC','PACKAGE_BODY'}
        paths=[_callee_parts(item['name']) if package else _callee_parts(item['name'])[-1:] for item in analyses]
        for item in analyses:
            path=_callee_parts(item['name']) if package else _callee_parts(item['name'])[-1:]
            prefixes={path[:i] for i in range(len(path)+1)}
            locals_={candidate[-1] for candidate in paths if candidate and candidate[:-1] in prefixes}
            for datatype in item['types']:
                ref=type_reference(datatype,default,declared_refs)
                if ref: refs.append(ref)
            for call in item['calls']:
                parts=_callee_parts(call)
                if len(parts)==1 and parts[0] in locals_: continue
                if len(parts)==1:
                    refs.append(DependencyReference(default,'CALLABLE',parts[0],'ROUTINE_CALL'))
                elif len(parts)==2:
                    packages=[ref for ref in declared_refs if ref['name']==parts[0] and ref['type'] in {'PACKAGE','PACKAGE_SPEC'}]
                    local=next((ref for ref in packages if ref['owner']==default),None)
                    bound=local or (packages[0] if len(packages)==1 else None)
                    refs.append(DependencyReference(bound['owner'],'PACKAGE_SPEC',parts[0],'ROUTINE_CALL') if bound else
                                DependencyReference(parts[0],'CALLABLE',parts[1],'ROUTINE_CALL'))
                elif len(parts)==3:
                    refs.append(DependencyReference(parts[0],'PACKAGE_SPEC',parts[1],'ROUTINE_CALL'))
    if declared and declared.state=='KNOWN' and not signature_only_spec(obj,projection):
        for ref in declared.value:
            kind={'PACKAGE':'PACKAGE_SPEC','TYPE':'TYPE_SPEC'}.get(ref['type'],ref['type'].replace(' ','_'))
            refs.append(DependencyReference(ref['owner'],kind,ref['name'],'SOURCE_DEPENDENCY'))
    tokens=code_tokens(obj.raw_ddl.decode()) if obj.raw_ddl else ()
    cte_ranges=_cte_ranges(tokens)
    for i,token in enumerate(tokens):
        # Sequence references in defaults/code are semantic prerequisites.
        if token.upper=='NEXTVAL' and i>=2 and tokens[i-1].text=='.':
            try:
                name=identifier(tokens[i-2])[0];owner=default
                if i>=4 and tokens[i-3].text=='.': owner=identifier(tokens[i-4])[0]
                refs.append(DependencyReference(owner,'SEQUENCE',name,'SEQUENCE_DEFAULT'))
            except ValueError: pass
        if token.upper in {'FROM','JOIN'} and i+1<len(tokens) and tokens[i+1].text!='(':
            # TABLE(collection_expression) is a SQL operator, not a relation
            # whose name is TABLE. Quoted "TABLE" stays a normal identifier.
            if i+2<len(tokens) and tokens[i+1].upper=='TABLE' and tokens[i+2].text=='(':
                continue
            try:
                name=identifier(tokens[i+1])[0];owner=default
                if i+3<len(tokens) and tokens[i+2].text=='.':
                    owner,name=name,identifier(tokens[i+3])[0]
                    boundary=i+4
                else:boundary=i+2
                if boundary<len(tokens) and tokens[boundary].text=='@':
                    refs.append(DependencyReference(owner,'DATABASE_LINK',name,'REMOTE_QUERY'))
                    continue
                if boundary==i+2 and any(alias==name and start<=i<end for alias,start,end in cte_ranges):
                    continue
                refs.append(DependencyReference(owner,'RELATION',name,'QUERY_RELATION',unqualified=boundary==i+2))
            except ValueError: pass
    return tuple(sorted(set(refs),key=lambda item:(item.owner,item.object_type,item.name,item.role,item.unqualified,item.columns)))
