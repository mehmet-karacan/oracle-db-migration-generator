"""Schema Compare aynı SQL'in saf lexer sonucunu sınırlı bellekte yeniden kullanır.

Ham metin ve token konumları aynen korunur. Önbellek Oracle gözlemi veya
parser doğrulaması tutmaz. Hatalı lexer sonucu ve çok büyük girdiler saklanmaz.
Tam token nesneleri yerine yalnız karakter konumları saklanır.

Author: Mehmet KARACAN
Date: 2026-11-09
"""
from collections import OrderedDict
from array import array
from functools import lru_cache
from threading import RLock

from .._vendor.analyzer_core.oracle.ddl_tokens import DdlToken,code_tokens as _lex_tokens

MIN_TEXT_BYTES=2048
MAX_ENTRY_BYTES=512*1024
MAX_ENTRY_TOKENS=120000
MAX_TOTAL_BYTES=16*1024*1024
MAX_TOTAL_TOKENS=2000000
MAX_ENTRIES=1024
_entries=OrderedDict()
_bytes=0
_tokens=0
_lock=RLock()


class _LexerFailure(ValueError):
    """Lexer hatasının kısa metin önbelleğinde saklanmasını önler.

    Author: Mehmet KARACAN
    Date: 2026-11-09
    """


@lru_cache(maxsize=512)
def _small_tokens(text):
    result=_lex_tokens(text)
    if result is None:raise _LexerFailure()
    return result


def clear_cache():
    """Yalnız bu süreçteki saf token kayıtlarını kaldırır."""
    global _bytes,_tokens
    with _lock:
        _entries.clear();_bytes=0;_tokens=0
        _small_tokens.cache_clear()


def cache_stats():
    """SQL metni içermeyen kayıt ve kapasite sayılarını döndürür."""
    with _lock:return {'entries':len(_entries),'bytes':_bytes,'tokens':_tokens,
                      'small_entries':_small_tokens.cache_info().currsize}


def analysis_tokens(text):
    """Aynı metin için aynı immutable token dizisini veya lexer hatasını döndürür."""
    global _bytes,_tokens
    if len(text)<=64:
        try:return _small_tokens(text)
        except _LexerFailure:return None
    if not MIN_TEXT_BYTES<=len(text)<=MAX_ENTRY_BYTES:
        return _lex_tokens(text)
    spans=None
    with _lock:
        entry=_entries.get(text)
        if entry is not None:
            _entries.move_to_end(text)
            spans=entry[0]
    if spans is not None:
        return tuple(DdlToken(text[spans[i]:spans[i+1]],spans[i],spans[i+1])
                     for i in range(0,len(spans),2))
    result=_lex_tokens(text)
    size=len(text.encode('utf-8'))
    if (result is None or size>min(MAX_ENTRY_BYTES,MAX_TOTAL_BYTES)
            or len(result)>min(MAX_ENTRY_TOKENS,MAX_TOTAL_TOKENS)):
        return result
    with _lock:
        if text in _entries:
            _entries.move_to_end(text)
            return result
        while _entries and (len(_entries)>=MAX_ENTRIES or _bytes+size>MAX_TOTAL_BYTES
                            or _tokens+len(result)>MAX_TOTAL_TOKENS):
            _,(removed,removed_size)=_entries.popitem(last=False)
            _bytes-=removed_size;_tokens-=len(removed)//2
        spans=array('I',(value for token in result for value in (token.start,token.end)))
        _entries[text]=(spans,size);_bytes+=size;_tokens+=len(result)
    return result
