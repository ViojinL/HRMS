from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0007_segment_active_and_overlap'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            UPDATE leave_time_segment s
            SET is_active = FALSE
            FROM leave_apply la
            WHERE s.leave_id = la.id
              AND la.apply_status IN ('completed','rejected');

            UPDATE leave_time_segment s
            SET is_active = TRUE
            FROM leave_apply la
            WHERE s.leave_id = la.id
              AND la.apply_status IN ('reviewing','approved');
            """,
            reverse_sql="""
            -- No-op rollback
            """,
        )
    ]
