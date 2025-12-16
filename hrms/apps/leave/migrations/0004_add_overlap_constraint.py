from django.db import migrations
from django.contrib.postgres.operations import BtreeGistExtension

class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0003_alter_leaveapply_create_by_alter_leaveapply_id_and_more'),
    ]

    operations = [
        BtreeGistExtension(),
        migrations.RunSQL(
            sql="""
            ALTER TABLE leave_time_segment
            ADD CONSTRAINT no_leave_overlap
            EXCLUDE USING gist (
                emp_id WITH =,
                tstzrange(leave_start_time, leave_end_time) WITH &&
            );
            """,
            reverse_sql="""
            ALTER TABLE leave_time_segment
            DROP CONSTRAINT IF EXISTS no_leave_overlap;
            """
        ),
    ]
