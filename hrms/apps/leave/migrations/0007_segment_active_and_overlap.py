from django.db import migrations, models


def seed_segment_active(apps, schema_editor):
    # Use raw SQL to avoid ORM join performance issues
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE leave_time_segment s
            SET is_active = CASE
                WHEN la.apply_status IN ('reviewing','approved') THEN TRUE
                ELSE FALSE
            END
            FROM leave_apply la
            WHERE s.leave_id = la.id;
            """
        )


def reverse_seed_segment_active(apps, schema_editor):
    # On rollback, default everything back to TRUE
    LeaveTimeSegment = apps.get_model("leave", "LeaveTimeSegment")
    LeaveTimeSegment.objects.update(is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ("leave", "0006_update_statuses"),
    ]

    operations = [
        migrations.AddField(
            model_name="leavetimesegment",
            name="is_active",
            field=models.BooleanField(
                default=True,
                verbose_name="占用冲突校验",
                help_text="True 时参与时间重叠校验；已拒绝/已完成后设为 False 以允许后续申请",
            ),
        ),
        migrations.RunSQL(
            sql="""
            ALTER TABLE leave_time_segment
            DROP CONSTRAINT IF EXISTS no_leave_overlap;
            """,
            reverse_sql="""
            ALTER TABLE leave_time_segment
            DROP CONSTRAINT IF EXISTS no_leave_overlap;
            """,
        ),
        migrations.RunSQL(
            sql="""
            ALTER TABLE leave_time_segment
            ADD CONSTRAINT no_leave_overlap
            EXCLUDE USING gist (
                emp_id WITH =,
                is_active WITH =,
                tstzrange(leave_start_time, leave_end_time) WITH &&
            );
            """,
            reverse_sql="""
            ALTER TABLE leave_time_segment
            DROP CONSTRAINT IF EXISTS no_leave_overlap;
            """,
        ),
        migrations.RunPython(seed_segment_active, reverse_seed_segment_active),
    ]
