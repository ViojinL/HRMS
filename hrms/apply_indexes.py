import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()


def apply_sql_file(file_path: str) -> None:
    print(f"Applying SQL from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Some drivers don't allow multiple statements in one execute.
    # We split on ';' naïvely, skipping empty statements.
    def _clean(stmt: str) -> str:
        lines = []
        for line in stmt.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('--'):
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    statements = []
    for raw in sql.split(';'):
        cleaned = _clean(raw)
        if cleaned:
            statements.append(cleaned)

    with connection.cursor() as cursor:
        for stmt in statements:
            cursor.execute(stmt)

    print("Done.")


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, 'db', 'sql', 'report_indexes.sql')
    apply_sql_file(sql_path)
