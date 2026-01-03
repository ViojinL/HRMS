from django.db import migrations, models


STATUS_MAP = {
    "pending": "reviewing",
    "approving": "reviewing",
    "cancelled": "rejected",
    "invalid": "rejected",
}


def forwards(apps, schema_editor):
    LeaveApply = apps.get_model("leave", "LeaveApply")
    for old, new in STATUS_MAP.items():
        LeaveApply.objects.filter(apply_status=old).update(apply_status=new)


def backwards(apps, schema_editor):
    # Best-effort rollback: map to reviewing unless previously rejected
    LeaveApply = apps.get_model("leave", "LeaveApply")
    LeaveApply.objects.filter(apply_status="reviewing").update(apply_status="pending")
    LeaveApply.objects.filter(apply_status="rejected").update(apply_status="cancelled")


class Migration(migrations.Migration):

    dependencies = [
        ("leave", "0005_check_status_flow"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leaveapply",
            name="apply_status",
            field=models.CharField(
                choices=[
                    ("reviewing", "审核中"),
                    ("approved", "已批准"),
                    ("rejected", "已拒绝"),
                    ("completed", "已完成"),
                ],
                default="reviewing",
                max_length=20,
                verbose_name="申请状态",
            ),
        ),
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION check_leave_status_flow()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.apply_status = OLD.apply_status THEN
                    RETURN NEW;
                END IF;

                -- 终态：已完成 / 已拒绝 不可再变更
                IF OLD.apply_status IN ('completed', 'rejected') THEN
                    RAISE EXCEPTION 'Cannot change status from % to %: Record is in final state', OLD.apply_status, NEW.apply_status;
                END IF;

                -- 审核中只能去 已批准 或 已拒绝
                IF OLD.apply_status = 'reviewing' AND NEW.apply_status NOT IN ('approved', 'rejected') THEN
                    RAISE EXCEPTION 'Invalid status transition: reviewing cannot go to %', NEW.apply_status;
                END IF;

                -- 已批准只能去 已完成
                IF OLD.apply_status = 'approved' AND NEW.apply_status <> 'completed' THEN
                    RAISE EXCEPTION 'Invalid status transition: approved cannot go to %', NEW.apply_status;
                END IF;

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trigger_check_leave_status ON leave_apply;
            CREATE TRIGGER trigger_check_leave_status
            BEFORE UPDATE OF apply_status ON leave_apply
            FOR EACH ROW
            EXECUTE FUNCTION check_leave_status_flow();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS trigger_check_leave_status ON leave_apply;
            DROP FUNCTION IF EXISTS check_leave_status_flow;
            """,
        ),
        migrations.RunPython(forwards, backwards),
    ]
