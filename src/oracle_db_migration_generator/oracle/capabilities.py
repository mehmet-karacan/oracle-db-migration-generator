"""Conservative, metadata-backed capabilities; no database mutation probes."""
from ..model.snapshot import KnownValue
import re


def collation_capabilities(rows,evidence_id):
    """Actual parameter observations; the 4000-byte floor is not proof."""
    parameters={row['name']:str(row['value']).upper() for row in rows} if rows is not None else {}
    if rows is not None and len(parameters)!=len(rows):parameters={}
    size=parameters.get('max_string_size')
    if size not in {'STANDARD','EXTENDED'}:size=None
    compatible=parameters.get('compatible')
    parts=re.fullmatch(r'(\d+)\.(\d+)(?:\.\d+)*',compatible or '')
    version=tuple(int(value) for value in parts.groups()) if parts else None
    enabled=(False if size=='STANDARD' or version is not None and version<(12,2)
             else True if size=='EXTENDED' and version is not None else None)
    ids=(evidence_id,)
    return {'collation_max_string_size':KnownValue('KNOWN' if size else 'UNKNOWN',size,ids),
            'collation_compatible':KnownValue('KNOWN' if version is not None else 'UNKNOWN',compatible if version is not None else None,ids),
            'data_bound_collation_enabled':KnownValue('KNOWN' if enabled is not None else 'UNKNOWN',enabled,ids)}


def describe_capabilities(version, nls_rows, evidence_id):
    ids = (evidence_id,)
    values = {row['parameter']: row['value'] for row in nls_rows} if nls_rows is not None else {}
    charset = values.get('NLS_CHARACTERSET')
    widths = {'AL32UTF8':4, 'UTF8':6, 'WE8MSWIN1252':1, 'WE8ISO8859P1':1,
              'WE8ISO8859P9':1, 'TR8MSWIN1254':1, 'US7ASCII':1, 'AL16UTF16':4}
    try:
        major = int(str(version).split('.')[0])
    except ValueError:
        major = None
    result = {'oracle_version': KnownValue('KNOWN', str(version), ids),
              'oracle_major': KnownValue('KNOWN' if major else 'UNKNOWN', major, ids),
              'database_charset': KnownValue('KNOWN' if charset else 'UNKNOWN', charset, ids),
              'max_bytes_per_character': KnownValue('KNOWN' if charset in widths else 'UNKNOWN', widths.get(charset), ids)}
    # STANDARD's limit is a safe floor for both STANDARD and EXTENDED. It does
    # not claim that the target's actual MAX_STRING_SIZE was observed.
    result['max_varchar2_bytes'] = KnownValue('KNOWN' if major and major >= 11 else 'UNKNOWN',
                                             4000 if major and major >= 11 else None, ids)
    result['max_varchar2_limit_basis'] = KnownValue('KNOWN', 'CONSERVATIVE_STANDARD_FLOOR', ids)
    return result
