import copy
import json
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path

import pytest

from oracle_db_migration_generator.config.loader import ConfigError, load_source_profile, load_targets
from oracle_db_migration_generator.model.identity import Identifier, ObjectIdentity
from oracle_db_migration_generator.model.snapshot import KnownValue

ROOT = Path(__file__).resolve().parents[2]


def write(tmp_path, document):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


@pytest.fixture
def registry():
    return json.loads((ROOT / "examples/targets.example.json").read_text(encoding="utf-8"))


def test_registry_all_discovers_three_targets(tmp_path, registry):
    targets = load_targets(write(tmp_path, registry), ("ALL",))
    assert len(targets) == 3
    assert len({t.id for t in targets}) == 3
    with pytest.raises(FrozenInstanceError):
        targets[0].id = "changed"


def test_registry_unknown_id_fails(tmp_path, registry):
    with pytest.raises(ConfigError) as exc:
        load_targets(write(tmp_path, registry), ("missing",))
    assert exc.value.exit_code == 30
    registry['targets'][0]['enabled'] = False
    with pytest.raises(ConfigError):
        load_targets(write(tmp_path, registry), ("DEMO-TEST",))


def test_explicit_catalog_reader_and_bounded_capture_timeout(tmp_path,registry):
    registry['targets'][0]['schema_mappings'][0]['metadata_reader']='AUDITOR'
    registry['targets'][0]['capture_timeout_seconds']=3600
    target=load_targets(write(tmp_path,registry),('DEMO-TEST',))[0]
    assert target.schema_mappings[0].metadata_reader=='AUDITOR'
    assert target.capture_timeout_seconds==3600
    assert target.schema_mappings[0].source_schema==target.schema_mappings[0].target_schema=='APP'


@pytest.mark.parametrize('reader',['','AUDITOR; SELECT 1','A.B',42])
def test_invalid_catalog_reader_is_rejected(tmp_path,registry,reader):
    registry['targets'][0]['schema_mappings'][0]['metadata_reader']=reader
    with pytest.raises(ConfigError):load_targets(write(tmp_path,registry),('DEMO-TEST',))


@pytest.mark.parametrize('timeout',[0,29,7201,False,30.5,'3600'])
def test_invalid_capture_timeout_is_rejected(tmp_path,registry,timeout):
    registry['targets'][0]['capture_timeout_seconds']=timeout
    with pytest.raises(ConfigError):load_targets(write(tmp_path,registry),('DEMO-TEST',))


@pytest.mark.parametrize("mode", ["both", "neither"])
def test_registry_requires_exactly_one_service_or_sid(tmp_path, registry, mode):
    endpoint = registry["targets"][0]["endpoint"]
    if mode == "both":
        endpoint["sid"] = "EXAMPLE"
    else:
        endpoint.pop("service_name")
    with pytest.raises(ConfigError):
        load_targets(write(tmp_path, registry), ("ALL",))


@pytest.mark.parametrize("mode", ["id", "mapping", "credential"])
def test_registry_duplicate_target_and_mapping_rejected(tmp_path, registry, mode):
    if mode == "id":
        registry["targets"].append(copy.deepcopy(registry["targets"][0]))
    else:
        mapping = copy.deepcopy(registry["targets"][0]["schema_mappings"][0])
        if mode == "credential":
            mapping['credential_id'] = 'other-credential'
        registry["targets"][0]["schema_mappings"].append(mapping)
    with pytest.raises(ConfigError):
        load_targets(write(tmp_path, registry), ("ALL",))


def test_empty_registry_is_not_success(tmp_path, registry):
    for target in registry["targets"]:
        target["enabled"] = False
    with pytest.raises(ConfigError):
        load_targets(write(tmp_path, registry), ("ALL",))
    registry["targets"] = []
    with pytest.raises(ConfigError):
        load_targets(write(tmp_path, registry), ("ALL",))


def test_secrets_are_not_serialized(tmp_path, registry):
    secret = "synthetic-sensitive-value"
    registry["targets"][0]["password"] = secret
    with pytest.raises(ConfigError) as exc:
        load_targets(write(tmp_path, registry), ("ALL",))
    assert secret not in str(exc.value)
    assert secret not in repr(exc.value)
    registry["targets"][0].pop("password")
    assert secret not in json.dumps(asdict(load_targets(write(tmp_path, registry), ("ALL",))[0]))


def test_absent_unknown_and_sql_null_are_distinct():
    absent = KnownValue("ABSENT", None, ("inventory-evidence",))
    unknown = KnownValue("UNKNOWN", None, ())
    sql_null = KnownValue("KNOWN", None, ("column-evidence",))
    assert len({absent, unknown, sql_null}) == 3
    with pytest.raises(ValueError):
        KnownValue("ABSENT", None, ())
    with pytest.raises(ValueError):
        KnownValue("UNKNOWN", "not-null", ())


def test_effective_identity_ignores_quoting_and_has_no_delimiter_collision():
    def key(owner, name):
        return ObjectIdentity("profile", Identifier.parse(owner), "TABLE", Identifier.parse(name), None).key
    assert key('APP', 'FOO') == key('"APP"', '"FOO"')
    assert key('APP', 'FOO') != key('APP', '"Foo"')
    assert key('"A|B"', 'C') != key('A', '"B|C"')


def test_source_profile_rejects_overlapping_and_duplicate_roots(tmp_path):
    document = json.loads((ROOT / "examples/source-profile.example.json").read_text(encoding="utf-8"))
    assert load_source_profile(write(tmp_path, document)).id
    document['schema_roots'].append({'path': document['schema_roots'][0]['path'] + '/nested', 'source_schema': 'OTHER'})
    with pytest.raises(ConfigError):
        load_source_profile(write(tmp_path, document))


@pytest.mark.parametrize('selected', [(), ('ALL', 'DEMO-TEST'), ('DEMO-TEST', 'DEMO-TEST')])
def test_ambiguous_selection_rejected(tmp_path, registry, selected):
    with pytest.raises(ConfigError):
        load_targets(write(tmp_path, registry), selected)


def test_credential_environment_key_collisions_rejected(tmp_path, registry):
    registry['targets'][0]['schema_mappings'][0]['credential_id'] = 'demo-key'
    registry['targets'][1]['schema_mappings'][0]['credential_id'] = 'demo_key'
    with pytest.raises(ConfigError, match='CREDENTIAL_ENV_KEY_COLLISION'):
        load_targets(write(tmp_path, registry), ('ALL',))
