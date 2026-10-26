from ..config.credentials import Credentials
from ..config.models import TargetConfig


def connect_read_only(target: TargetConfig, credentials: Credentials):
    import oracledb

    thin = oracledb.is_thin_mode()
    if (target.driver_mode == 'thin') != thin:
        raise ValueError('ORACLE_DRIVER_MODE_MISMATCH')
    endpoint = target.endpoint
    from ..config.runtime import current_settings
    settings=current_settings()
    params = oracledb.ConnectParams(host=endpoint.host, port=endpoint.port,
                                   service_name=endpoint.service_name, sid=endpoint.sid,
                                   tcp_connect_timeout=settings.get('connect_timeout_seconds',8), retry_count=0)
    connection = oracledb.connect(user=credentials.username, password=credentials.password, params=params)
    connection.autocommit = False
    connection.call_timeout = settings.get('call_timeout_ms',15000)
    return connection
