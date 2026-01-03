from django.db import migrations, models


def _map_resigning_to_active(apps, schema_editor):
    Employee = apps.get_model("employee", "Employee")
    Employee.objects.filter(emp_status="resigning").update(emp_status="active")


class Migration(migrations.Migration):

    dependencies = [
        ("employee", "0004_alter_employee_create_by_alter_employee_id_and_more"),
    ]

    operations = [
        migrations.RunPython(
            _map_resigning_to_active, reverse_code=migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="employee",
            name="emp_status",
            field=models.CharField(
                choices=[
                    ("probation", "试用期"),
                    ("active", "在职"),
                    ("resigned", "离职"),
                    ("suspended", "停薪留职"),
                ],
                max_length=20,
                verbose_name="员工状态",
            ),
        ),
    ]
