from copy import deepcopy
from html.parser import HTMLParser

from oracle_db_migration_generator.reporting.render import render_email, render_reports, render_run_reports
from oracle_db_migration_generator.reporting.view import build_run_view
from tests.unit.test_report_views import inputs


def visible(raw):
    class Text(HTMLParser):
        def __init__(self):
            super().__init__(); self.parts = []; self.hidden = 0
        def handle_starttag(self, tag, attrs):
            if tag in {'details', 'style'}: self.hidden += 1
        def handle_endtag(self, tag):
            if tag in {'details', 'style'}: self.hidden -= 1
        def handle_data(self, data):
            if not self.hidden: self.parts.append(data)
    parser = Text(); parser.feed(raw.decode())
    return ' '.join(parser.parts)


def blocked_inputs():
    run, plans = inputs(); plan = plans['TARGET-000']
    run['targets'][0].update(status='BLOCKED', difference_count=None)
    plan['status'] = 'BLOCKED'
    plan['counts'].update(ready_operations=1266, review_operations=633, blocked_operations=251)
    op = plan['operations'][0]
    op.update(decision='BLOCKED', kind='COMMENT', sql=None,
              reason_codes=['DEPENDENCY_UNVERIFIED', 'SET_VERIFIED_COMMENT'],
              reason_tr='APP.ORDERS (PRICE) [TABLE]: bağımlı nesnenin gerekli işlemi hazır değil: REVIEW / BLOCKED; APP.ORDERS (PRICE) [TABLE]: hedefte bulunamadı ve oluşturulmasını sağlayan kaynak işlemi yok.')
    op['object'].update(object_type='COMMENT', display_name='ORDERS.PRICE')
    return run, plans


def test_manager_reports_show_plain_status_and_specific_reason_below_it():
    run, plans = blocked_inputs(); before = deepcopy((run, plans))
    view = build_run_view(run, plans)
    pages = [render_email(view), render_run_reports(view)['index.html'],
             render_reports(plans['TARGET-000'], {})['index.html']]
    for raw in pages:
        text = visible(raw)
        assert 'DDL üretilemedi' in text
        assert not any(code in text for code in ('BLOCKED', '[TABLE]', 'REVIEW_REQUIRED', 'COMMENT', 'AUTO_GENERATED'))
        assert 'APP.ORDERS (PRICE)' in text and 'hedefte bulunamadı' in text
        assert 'Açıklama' in text and '251' in text and '1.266' in text
        assert text.index('DDL üretilemedi') < text.index('APP.ORDERS (PRICE)')
    assert (run, plans) == before


def test_unknown_definition_does_not_become_a_missing_object_claim():
    run, plans = blocked_inputs(); op = plans['TARGET-000']['operations'][0]
    op.update(reason_codes=['OBJECT_METADATA_INCOMPLETE'],
              reason_tr='Eksik metadata veya doğrulanmamış yokluk güvenli SQL üretimini engelliyor.')
    text = visible(render_email(build_run_view(run, plans)))
    assert 'Nesnenin tanımı veya hedefte bulunup bulunmadığı doğrulanamadı.' in text
    assert 'hedefte bulunamadı' not in text and 'Bulunan fark' in text


def test_target_with_ready_sql_is_reported_as_partially_ready():
    run, plans = blocked_inputs()
    view = build_run_view(run, plans)
    assert view['targets'][0]['display_status'] == 'DDL kısmen hazır'
    assert 'DDL kısmen hazır' in visible(render_reports(plans['TARGET-000'], {})['index.html'])
    plans['TARGET-000']['counts']['ready_operations'] = 0
    assert build_run_view(run, plans)['targets'][0]['display_status'] == 'DDL üretilemedi'


def test_known_dependency_reason_is_short_unique_and_escaped():
    run, plans = blocked_inputs(); op = plans['TARGET-000']['operations'][0]
    op['reason_tr'] = op['reason_tr'].replace('ORDERS', '<script>')
    view = build_run_view(run, plans)
    reason = view['important_objects'][0]['reason']
    assert len(reason) <= 240 and reason.count('APP.<script> (PRICE)') == 1
    html = render_email(view).decode()
    assert '&lt;script&gt;' in html and '<script>' not in html


def test_every_real_blocker_category_has_a_specific_short_explanation():
    run, plans = blocked_inputs(); op = plans['TARGET-000']['operations'][0]
    for code, phrase in [('UNKNOWN_SOURCE_SEMANTICS', 'kolon tipi'),
                         ('COLUMN_METADATA_UNKNOWN', 'Kolon'),
                         ('INDEX_DEFINITION_UNVERIFIED', 'İndeks'),
                         ('RESERVED_INTERNAL_OBJECT', 'anahtar'),
                         ('BLOCKED_UNSUPPORTED_FEATURE', 'özel tablo')]:
        op['reason_codes'] = [code]
        reason = build_run_view(run, plans)['important_objects'][0]['reason']
        assert phrase in reason and len(reason) <= 240


def test_dependency_status_at_sentence_end_is_translated_without_renaming_objects():
    run, plans = blocked_inputs(); op = plans['TARGET-000']['operations'][0]
    op.update(reason_codes=['PREREQUISITE_NOT_READY'],
              reason_tr='APP.BLOCKED [FUNCTION]: gerekli CREATE işlemi BLOCKED.')
    reason = build_run_view(run, plans)['important_objects'][0]['reason']
    assert reason == 'APP.BLOCKED: oluşturma işlemi için DDL üretilemedi.'


def test_mail_reason_stays_in_the_object_cell():
    run, plans = blocked_inputs()
    html = render_email(build_run_view(run, plans)).decode()
    class Rows(HTMLParser):
        def __init__(self):
            super().__init__(); self.rows=[]; self.row=None; self.cell=None
        def handle_starttag(self,tag,attrs):
            if tag=='tr': self.row=[]
            elif tag=='td' and self.row is not None: self.cell=[]
        def handle_data(self,data):
            if self.cell is not None:self.cell.append(data)
        def handle_endtag(self,tag):
            if tag=='td' and self.cell is not None:
                self.row.append(' '.join(self.cell));self.cell=None
            elif tag=='tr' and self.row is not None:
                self.rows.append(self.row);self.row=None
    parser=Rows();parser.feed(html)
    row=next(row for row in parser.rows if row and 'APP.ORDERS.PRICE' in row[0])
    assert len(row)==4
    assert 'hedefte bulunamadı' in row[0]
    assert all('hedefte bulunamadı' not in cell for cell in row[1:])


def test_mail_reason_summarizes_complex_table_dependency_without_repeating_the_object():
    run,plans=blocked_inputs()
    op=plans['TARGET-000']['operations'][0]
    op['reason_tr']='APP.ORDERS (PRICE) [TABLE]: hedefte bulunamadı; bağlı nesne için DDL üretilemedi: Partition, LOB, IOT, external veya cluster özelliği sade tabloya dönüştürülemez.'
    view=build_run_view(run,plans)
    row=view['important_objects'][0]
    assert row['mail_reason']=='Bağlı tablonun özel yapısı için DDL desteği gerekiyor.'
    assert 'Partition, LOB' in row['reason']
