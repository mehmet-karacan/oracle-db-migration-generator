"""Schema Compare sabit JSON sözleşmelerini derleyerek doğrulama yükünü azaltır.

Yalnız ortak schema anahtarları hızlandırılır. Bilinmeyen özellik standart
2020 doğrulayıcısına bırakılır. Girdiye varsayılan alan veya değer eklenmez.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
import fastjsonschema

SUPPORTED=frozenset(('$schema','$id','title','description','type','properties','required',
    'additionalProperties','items','enum','const','anyOf','allOf','oneOf','not','if','then','else',
    'pattern','minLength','maxLength','minimum','maximum','exclusiveMinimum','exclusiveMaximum',
    'minItems','maxItems','uniqueItems','minProperties','maxProperties','format','default'))


def compatible(schema):
    """2020 sözleşmesinde yalnız draft 7 ile ortak kurallar bulunduğunu denetler."""
    if isinstance(schema,bool):return True
    if not isinstance(schema,dict) or set(schema)-SUPPORTED:return False
    if any(not compatible(child) for child in schema.get('properties',{}).values()):return False
    for name in ('additionalProperties','items','not','if','then','else'):
        if name in schema and not compatible(schema[name]):return False
    return all(compatible(child) for name in ('anyOf','allOf','oneOf') for child in schema.get(name,()))


def compile_checked_schema(schema):
    """Uygun sabit sözleşme için girdiyi değiştirmeyen doğrulayıcı döndürür."""
    if not compatible(schema):return None
    definition={**schema,'$schema':'http://json-schema.org/draft-07/schema#'}
    try:
        compiled=fastjsonschema.compile(definition,use_default=False,use_formats=False)
    except fastjsonschema.JsonSchemaException:
        return None
    def validate(document):
        try:compiled(document)
        except fastjsonschema.JsonSchemaException:
            raise ValueError('CONFIG_SCHEMA_INVALID') from None
    return validate
