"""Schema Compare hızlı sözleşme kontrolünü standart doğrulayıcıyla karşılaştırır.

Geçerli girdi değiştirilmez. Yeni schema özellikleri standart yola döner.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from oracle_db_migration_generator.config import loader


def test_existing_contract_does_not_repeat_recursive_validation(monkeypatch):
    data=json.loads(Path('examples/source-profile.example.json').read_bytes())
    before=deepcopy(data)
    monkeypatch.setattr(Draft202012Validator,'iter_errors',lambda *a,**k:pytest.fail('valid contract used recursive validation'))
    loader.validate_document(data,'source-profile.schema.json')
    assert data==before


def test_fast_schema_has_same_acceptance_for_contract_values():
    from oracle_db_migration_generator.config.schema_validation import compile_checked_schema
    schema={'type':'object','additionalProperties':False,'properties':{
        'state':{'enum':['KNOWN','UNKNOWN']},'count':{'type':'integer','minimum':0},
        'value':{'anyOf':[{'type':'string','pattern':'^[A-Z]+$'},{'type':'null'}]},
        'items':{'type':'array','uniqueItems':True,'items':{'type':'integer'}},
        'known':{'type':'boolean'}},'required':['state','count'],
        'if':{'properties':{'state':{'const':'UNKNOWN'}}},'then':{'properties':{'value':{'type':'null'}}}}
    fast=compile_checked_schema(schema)
    assert fast is not None
    baseline={'state':'KNOWN','count':1,'value':'ABC','items':[1,2],'known':True}
    values=[None,True,False,0,1,1.0,-1,{},[],[1,True],[1,1],[1,2],'','ABC','ABC\n','UNKNOWN']
    for key in baseline:
        for value in values:
            data={**baseline,key:value};before=deepcopy(data)
            try:fast(data);accepted=True
            except ValueError:accepted=False
            # Hızlı reddin standart yolda yeniden kontrolü dış katmanda yapılır.
            assert not accepted or Draft202012Validator(schema).is_valid(data),(key,value)
            assert data==before


@pytest.mark.parametrize('keyword',['unevaluatedProperties','prefixItems','$ref','dependentSchemas'])
def test_new_dialect_keywords_cannot_be_silently_ignored(keyword):
    from oracle_db_migration_generator.config.schema_validation import compile_checked_schema
    assert compile_checked_schema({'type':'object',keyword:False}) is None
