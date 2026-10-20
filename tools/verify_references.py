"""Read-only A00 reference check; drift is reported with exit 10."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from oracle_db_migration_generator.config.loader import read_json
from oracle_db_migration_generator.references import validate_project_root, verify_references


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT / 'output/reference-check.json')
    args = parser.parse_args()
    context = read_json(ROOT / '.local/session-context.json')
    validate_project_root(ROOT, context['generator_repository'])
    report = verify_references(read_json(ROOT / 'reference-lock.json'), context['reference_projects'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], **report['summary']}))
    return 10 if report['status'] != 'MATCHED' else 0


if __name__ == '__main__':
    raise SystemExit(main())
