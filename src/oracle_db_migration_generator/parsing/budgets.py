from ..config.runtime import current_settings


def parser_timeout(size,kind):
    settings=current_settings()
    if kind=='PACKAGE_BODY' and size>128*1024:return settings.get('parser_package_seconds',240)
    if size>24*1024:return settings.get('parser_large_seconds',120)
    return settings.get('parser_regular_seconds',30)
