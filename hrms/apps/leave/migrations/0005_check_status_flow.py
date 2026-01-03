from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("leave", "0004_add_overlap_constraint"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION check_leave_status_flow()
            RETURNS TRIGGER AS $$
            BEGIN
                -- 允许不做修改的情况
                IF NEW.apply_status = OLD.apply_status THEN
                    RETURN NEW;
                END IF;

                -- 规则1: approved/rejected/cancelled 是终态，不可更改
                IF OLD.apply_status IN ('approved', 'rejected', 'cancelled') THEN
                    RAISE EXCEPTION 'Cannot change status from % to %: Record is in final state', OLD.apply_status, NEW.apply_status;
                END IF;

                -- 规则2: pending 只能流转到 approved, rejected, cancelled
                IF OLD.apply_status = 'pending' AND NEW.apply_status NOT IN ('approved', 'rejected', 'cancelled') THEN
                    RAISE EXCEPTION 'Invalid status transition: pending cannot go to %', NEW.apply_status;
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
    ]
