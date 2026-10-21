"""Complete package projection from the already verified bounded parse tree."""
from dataclasses import replace

from .._vendor.analyzer_core.oracle import package as vendor
from .._vendor.analyzer_core.oracle.ddl_tokens import code_tokens
from .._vendor.analyzer_core.oracle.projections import Projection


def package_projection(occurrence, source, root):
    """Keep nested routines as qualified lexical members, including their facts.

    The Analyzer's 128KB cap protects its independent second parse. This adapter
    only accepts the tree verified inside Generator's bounded worker, so there is
    no second parse and no reason to discard the verified larger source.
    """
    if root is None:
        raise ValueError('PACKAGE_VERIFIED_TREE_REQUIRED')
    kind=occurrence.object_type
    expected=vendor.PlSqlParser.Create_packageContext if kind=='PACKAGE_SPEC' else vendor.PlSqlParser.Create_package_bodyContext
    matches=[node for node in vendor._walk(root) if isinstance(node,expected)]
    if len(matches)!=1:
        raise ValueError('PACKAGE_IDENTITY_UNRESOLVED')
    package=matches[0]
    members=package.package_obj_spec() if kind=='PACKAGE_SPEC' else package.package_obj_body()
    declarations={key:[] for key in ('type_declaration','constant','variable_declaration','cursor_declaration','exception_declaration','pragma_declaration')}
    routines=[]
    routine_types=(vendor.PlSqlParser.Procedure_bodyContext,vendor.PlSqlParser.Function_bodyContext)
    def collect(context, prefix='', body=True):
        routine=vendor._routine(source,context,body=body)
        name=prefix+routine.name
        routines.append(replace(routine,name=name))
        if body:
            def nested(node):
                for child in node.getChildren():
                    if isinstance(child,routine_types):
                        collect(child,name+'.')
                    elif isinstance(child,vendor.ParserRuleContext):
                        nested(child)
            nested(context)
    for member in members:
        for method in ('procedure_spec','function_spec','procedure_body','function_body'):
            context=getattr(member,method,lambda:None)()
            if context is not None:collect(context,body=method.endswith('_body'))
        for method in declarations:
            if method=='constant':continue
            context=getattr(member,method,lambda:None)()
            if context is not None:
                value=vendor._span(source,context) or ''
                tokens=code_tokens(value) if method=='variable_declaration' else ()
                destination='constant' if any(token.upper=='CONSTANT' for token in tokens or ()) else method
                declarations[destination].append(value)
    tokens=code_tokens(source) or ()
    prefix=[]
    for token in tokens:
        if token.upper=='PACKAGE':break
        prefix.append(token.upper)
    props={'schema':occurrence.raw_schema,'name':occurrence.raw_name,
           'editionable':'NONEDITIONABLE' if 'NONEDITIONABLE' in prefix else 'EDITIONABLE' if 'EDITIONABLE' in prefix else None,
           'authid':vendor._span(source,package.invoker_rights_clause()) if kind=='PACKAGE_SPEC' else None,
           'routines':tuple(routines),'declarations':{key:tuple(values) for key,values in declarations.items()},
           'initialization':vendor._span(source,package.seq_of_statements()) if kind=='PACKAGE_BODY' else None}
    return Projection(occurrence.object_key,kind,props,'structural')
