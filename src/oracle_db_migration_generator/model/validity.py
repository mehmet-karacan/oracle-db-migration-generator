"""INVALID is an observed warning, separate from missing metadata."""


def report_only_invalid_ddl(obj):
    """Recognize captured INVALID text with parser-only diagnostics.

    This does not make the definition known. Only an untouched target-only
    object or an existence-only reference can use this reporting exception.
    Access failures, missing bytes and incomplete dictionary remain failures.
    """
    status=obj.properties.get('object_status')
    return bool(status and status.state=='KNOWN' and status.value=='INVALID'
                and obj.raw_ddl and obj.ddl_sha256
                and obj.coverage.inventory==obj.coverage.dictionary=='COMPLETE'
                and obj.coverage.ddl=='PARTIAL' and obj.coverage.diagnostics
                and set(obj.coverage.diagnostics)<={'PARSER_NOT_VERIFIED','PARSER_SYNTAX_ERROR'})
