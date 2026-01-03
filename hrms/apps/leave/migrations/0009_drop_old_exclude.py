from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("leave", "0008_fix_segment_flags"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE leave_time_segment
            DROP CONSTRAINT IF EXISTS exclude_emp_leave_time;
            """,
            reverse_sql="""
            ALTER TABLE leave_time_segment
            ADD CONSTRAINT exclude_emp_leave_time
            EXCLUDE USING gist (
                emp_id WITH =,
                tstzrange(leave_start_time, leave_end_time) WITH &&
            );
            """,
        ),
    ]
