import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()


def apply_sql_file(file_path: str) -> None:
    print(f"Applying SQL from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    with connection.cursor() as cursor:
        cursor.execute(sql)

    print("Done.")


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, 'db', 'sql', 'report_views.sql')
    apply_sql_file(sql_path)
