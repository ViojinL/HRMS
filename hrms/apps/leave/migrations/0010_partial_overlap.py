from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0009_drop_old_exclude'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE leave_time_segment
            DROP CONSTRAINT IF EXISTS no_leave_overlap;

            ALTER TABLE leave_time_segment
            ADD CONSTRAINT no_leave_overlap
            EXCLUDE USING gist (
                emp_id WITH =,
                tstzrange(leave_start_time, leave_end_time) WITH &&
            )
            WHERE (is_active);
            """,
            reverse_sql="""
            ALTER TABLE leave_time_segment
            DROP CONSTRAINT IF EXISTS no_leave_overlap;

            ALTER TABLE leave_time_segment
            ADD CONSTRAINT no_leave_overlap
            EXCLUDE USING gist (
                emp_id WITH =,
                is_active WITH =,
                tstzrange(leave_start_time, leave_end_time) WITH &&
            );
            """,
        ),
    ]
