"""Oracle's shared object namespace, independent of routine review gates."""
SHARED_NAMESPACE=frozenset({'TABLE','VIEW','MATERIALIZED_VIEW','SEQUENCE','PACKAGE_SPEC',
    'PROCEDURE','FUNCTION','TYPE_SPEC','SYNONYM'})


def namespace_conflicts(context,identity):
    if identity.object_type not in SHARED_NAMESPACE:return ()
    return tuple(obj for obj in context.target.objects
        if obj.identity.owner.effective_name==identity.owner.effective_name
        and obj.identity.name.effective_name==identity.name.effective_name
        and obj.identity.object_type in SHARED_NAMESPACE and obj.identity.object_type!=identity.object_type)


def conflict_description(identity,conflicts):
    return (identity.owner.effective_name+'.'+identity.name.effective_name+': hedefte '+
        ', '.join(sorted({obj.identity.object_type for obj in conflicts}))+
        ' mevcut. Kaynak '+identity.object_type+' aynı Oracle ad alanında oluşturulamaz.')
