"""Links require positive reachability evidence and immutable revision identity."""
import re
from dataclasses import dataclass
from urllib.parse import urlsplit


def safe_https(url, hosts):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in hosts or parsed.username or parsed.password
            or parsed.fragment or parsed.port not in (None,443) or any(c in url for c in '\r\n\\')
            or any(p in {'.','..'} for p in parsed.path.split('/'))):
        raise ValueError('PUBLICATION_URL_UNSAFE')
    return parsed


@dataclass(frozen=True)
class ArchiveLink:
    url: str
    note: str = 'Git yayını doğrulanmadı; erişilebilir sabit Jenkins arşivi kullanılıyor.'


def verified_archive(url, allowed_hosts, check, *, build_url):
    try:
        p = safe_https(url, allowed_hosts)
        build = safe_https(build_url, allowed_hosts)
        if build.query or not re.fullmatch(r'.*/[1-9][0-9]*/',build.path): return None
        if p.query or not url.startswith(build_url+'artifact/') or not re.search(r'/[1-9][0-9]*/artifact/.+', p.path): return None
        if not check(url): return None
        return ArchiveLink(url)
    except (ValueError, OSError): return None
