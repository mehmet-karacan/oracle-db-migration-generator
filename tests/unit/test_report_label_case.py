"""Şema Karşılaştırma etiketlerinin baş harflerini ve değişmeyen nesne kimliklerini sınar.

Örnek değerler kullanılır, gerçek Oracle veya Jenkins bağlantısı açılmaz.

Author: Mehmet KARACAN
Date: 2026-11-07
"""
import pytest

from oracle_db_migration_generator.reporting.labels import type_label, kind_label, status_label, object_label, _plain_reason


@pytest.mark.parametrize('code,expected', [
    ('TYPE_SPEC', 'Veri Tipi'), ('TYPE_BODY', 'Veri Tipi Gövdesi'),
    ('PACKAGE_SPEC', 'Paket Tanımı'), ('PACKAGE_BODY', 'Paket Gövdesi'),
    ('SEQUENCE', 'Sıra Numarası'), ('MATERIALIZED_VIEW', 'Saklanan Görünüm'),
    ('SYNONYM', 'Nesne Takma Adı'), ('INDEX', 'İndeks'),
])
def test_type_labels_use_consistent_heading_capitals(code, expected):
    assert type_label(code) == expected


def test_action_and_status_labels_use_the_same_heading_style():
    assert kind_label('ADD_COLUMN') == 'Kolon Ekleme'
    assert status_label('REVIEW_REQUIRED') == 'İnceleme Gerekli'
    assert status_label('READY') == 'DDL Hazır'


def test_heading_case_does_not_modify_object_identity_or_explanation_sentences():
    obj = {'owner': 'INNOVA_ODI', 'name': 'mixed_Name', 'object_type': 'TABLE'}
    assert object_label(obj) == 'INNOVA_ODI.mixed_Name'
    assert _plain_reason('PACKAGE_SPEC hedefte bulunamadı.') == 'paket tanımı hedefte bulunamadı.'
