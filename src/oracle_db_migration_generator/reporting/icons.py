"""Şema Karşılaştırma ölçülerini tema renkleriyle eşleşen Lucide ikonlarıyla gösterir.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
import base64
import json
from functools import lru_cache
from importlib.resources import files

from markupsafe import Markup


_catalog = json.loads(files(__package__).joinpath('assets/report-icons.json').read_text(encoding='utf-8'))
ICONS = _catalog['icons']
TYPE_ROLES = _catalog.get('type_roles', {})
ICON_NAMES = frozenset(ICONS)


@lru_cache(maxsize=128)
def _image_source(name, accent):
    variant = 'semantic' if accent else 'muted'
    raw = files(__package__).joinpath('assets', f'report-icon-{name}-{variant}.png').read_bytes()
    return 'data:image/png;base64,' + base64.b64encode(raw).decode('ascii')


def report_icon(name, size=22, *, accent=True, asset_prefix=None):
    """Paketli ikonları varsayılan renkli görselle ve boş alternatif metinle gösterir."""
    if name not in ICON_NAMES or type(size) is not int or not 12 <= size <= 32:
        raise ValueError('REPORT_ICON_INVALID')
    if asset_prefix is not None and asset_prefix not in ('', '../'):
        raise ValueError('REPORT_ICON_PREFIX_INVALID')
    variant = 'semantic' if accent else 'muted'
    icon = ICONS[name]
    tone = icon['tone'] if accent else 'neutral'
    source = (_image_source(name, bool(accent)) if asset_prefix is None
              else f'{asset_prefix}assets/report-icon-{name}-{variant}.png')
    return Markup(f'<img class="report-icon lucide lucide-{icon["name"]}" data-report-icon="{name}" '
                  f'data-icon-set="lucide" data-icon-name="{icon["name"]}" data-tone="{tone}" '
                  f'src="{source}" width="{size}" height="{size}" '
                  f'alt="" aria-hidden="true" style="display:inline-block;width:{size}px;height:{size}px;'
                  'vertical-align:middle;margin-right:8px;border:0">')


def metric_icon(index, catalog_known):
    """Özet kartının gerçek ölçüsüne uygun simgeyi seçer."""
    return ('database', 'compare', 'code', 'scan' if catalog_known else 'review', 'document')[index]


def report_type_icon(label, size=16, *, asset_prefix=None):
    """Tür adını renkli zeminli ve koyu fonda da seçilen bir Lucide simgesiyle eşleştirir."""
    role = TYPE_ROLES.get(str(label).casefold().replace('\u0307', ''), 'object-other')
    return report_icon(role, size, accent=True, asset_prefix=asset_prefix)


def icon_assets():
    """Web raporuyla taşınacak yerel ikon dosyalarını verir."""
    return {f'assets/report-icon-{name}-{variant}.png':
            files(__package__).joinpath('assets', f'report-icon-{name}-{variant}.png').read_bytes()
            for name in sorted(ICON_NAMES) for variant in ('semantic', 'muted')}
