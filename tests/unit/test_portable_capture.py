from pathlib import Path
import pytest
from oracle_db_migration_generator.portable.selection import CaptureFilter
from oracle_db_migration_generator.portable.builder import prepare_capture


def test_independent_filters_and_table_alias():
    scope=CaptureFilter.from_dict({'schemas':['app'],'table_names':['orders'],'data_types':['varchar2']})
    assert scope.schemas==('APP',) and scope.object_types==('TABLE',) and scope.object_names==('ORDERS',)
    assert scope.data_types==('VARCHAR2',) and scope.include_related
    quoted=CaptureFilter.from_dict({'schemas':['APP'],'object_names':['"Mixed Case"']})
    assert quoted.object_names==('Mixed Case',)
    with pytest.raises(ValueError):CaptureFilter.from_dict({'schemas':['APP'],'object_types':['TABLE'],'table_names':['A'],'object_names':['B']})
    with pytest.raises(ValueError):CaptureFilter.from_dict({'schemas':['APP'],'data_types':['NUMBER'],'object_types':['PACKAGE_BODY']})
    with pytest.raises(ValueError):CaptureFilter.from_dict({'schemas':['APP'],'object_names':['A\nDROP TABLE X']})


def test_generated_request_uses_encoded_binds_and_keeps_sql_data_untrusted(tmp_path):
    selection={'schemas':['APP'],'object_types':['TABLE'],'object_names':['"a\'b&c"'],'environment':'Prod & UAT'}
    result=prepare_capture(tmp_path/'capture',selection)
    request=(result/'run_export.sql').read_text(encoding='utf-8')
    assert 'SET DEFINE OFF' in request and ':p_schemas' in request
    assert "a'b&c" not in request and 'Prod & UAT' not in request
    assert 'HEXTORAW(' in request and '@collect.sql' in request
    collector=(result/'collect.sql').read_text(encoding='utf-8')
    assert 'DBMS_SQL.BIND_VARIABLE' in collector and 'DBMS_METADATA.GET_DDL' in collector
    assert 'CREATE TABLE' not in collector.upper() and 'EXECUTE IMMEDIATE' not in collector.upper()
    assert (result/'New-Capture.ps1').is_file() and (result/'README.md').is_file()
    with pytest.raises(ValueError):prepare_capture(result,selection)


def test_cli_package_and_import_are_offline(tmp_path,capsys):
    from oracle_db_migration_generator.cli import main
    from test_portable_stream import records,packet
    package=tmp_path/'package'
    assert main(['prepare-capture','--output',str(package),'--schema','APP','--table-name','DEMO'])==0
    assert (package/'collect.sql').is_file()
    capture=tmp_path/'capture.odmg.jsonl';capture.write_bytes(packet(records()))
    profile=Path(__file__).resolve().parents[2]/'examples/source-profile.example.json'
    assert main(['import-capture','--input',str(capture),'--source-profile',str(profile),'--side','SOURCE','--connection-id','portable-source','--output',str(tmp_path/'source')])==0
    assert (tmp_path/'source'/'source-snapshot.json').is_file()


def test_target_capture_does_not_drop_objects_whose_data_type_changed():
    from oracle_db_migration_generator.portable.builder import package_files
    scope=CaptureFilter.from_dict({'schemas':['"MixedOwner"'],'object_types':['TABLE'],'object_names':['"Mixed Name"'],
        'data_types':['TIMESTAMP WITH TIME ZONE'],'filter_side':'TARGET'})
    assert CaptureFilter.from_dict(scope.to_dict())==scope
    package=package_files(scope)
    assert "IF v_p_filter_side='SOURCE' AND v_p_data_types" in package['collect.sql']
    request=package['run_export.sql']
    assert 'Mixed Name' not in request and 'MixedOwner' not in request
    assert '4D69786564204E616D65' in request  # Exact effective name, without extra quote characters.
    assert '224D69786564204E616D6522' not in request


def test_sqlplus_standard_binds_and_root_inventory_are_portable():
    from oracle_db_migration_generator.portable.builder import package_files
    files=package_files({'schemas':['APP'],'object_types':['TABLE']})
    assert 'VARCHAR2(32767)' not in files['run_export.sql']
    assert 'VARCHAR2(4000 BYTE)' not in files['run_export.sql']
    assert 'VARIABLE p_schemas CLOB' in files['run_export.sql']
    assert 'VARIABLE p_schemas' in files['New-Capture.ps1'] or ' CLOB' in files['New-Capture.ps1']
    assert 'v_p_schemas VARCHAR2(32767) := :p_schemas' in files['collect.sql']
    main=files['collect.sql'].split('BEGIN\n    :odmg_exit_code:=20;',1)[1]
    assert 'DBMS_OUTPUT.ENABLE(NULL)' in main
    reset="DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'DEFAULT',TRUE)"
    assert reset in main
    assert main.index(reset) < main.index('capture_schema;')
    assert "add_query('session_calendar'" in files['collect.sql']
    assert "add_query('dependency_objects'" in files['collect.sql']
    assert 'd.owner = :owner' in files['collect.sql'] and 'o.subobject_name IS NULL' in files['collect.sql']
    assert "RAISE_APPLICATION_ERROR(-20011,'CAPTURE_INVENTORY_CHANGED')" in files['collect.sql']
    assert 'VARCHAR2(32767)' not in files['New-Capture.ps1']
    assert files['collect.sql'].lower().count('and subobject_name is null')==2
    with pytest.raises(ValueError,match='CAPTURE_FILTER_BYTE_LIMIT'):
        CaptureFilter.from_dict({'object_names':['X'+str(i)+'A'*100 for i in range(100)]})
