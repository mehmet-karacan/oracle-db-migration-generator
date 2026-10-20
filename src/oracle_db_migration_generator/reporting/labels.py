"""Human labels preserve canonical identity and use only recorded parent facts."""


def object_label(obj):
    if obj['object_type'] in {'COMMENT','GRANT'}:
        name=obj.get('display_name')
        if not name:return obj['object_type']+' (bağlı nesne doğrulanamadı)'
    else:name=obj['name']
    return obj['owner']+'.'+name
