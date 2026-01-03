from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("performance", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="performancecycle",
            name="attendance_weight",
            field=models.PositiveSmallIntegerField(
                default=50,
                help_text="用于规则计算，0-100",
                verbose_name="出勤率占比(%)",
            ),
        ),
        migrations.AddField(
            model_name="performancecycle",
            name="leave_weight",
            field=models.PositiveSmallIntegerField(
                default=50,
                help_text="用于规则计算，0-100",
                verbose_name="请假率占比(%)",
            ),
        ),
        migrations.AddField(
            model_name="performanceevaluation",
            name="attendance_rate",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                help_text="0-1 之间",
                max_digits=6,
                null=True,
                verbose_name="出勤率",
            ),
        ),
        migrations.AddField(
            model_name="performanceevaluation",
            name="leave_rate",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                help_text="0-1 之间",
                max_digits=6,
                null=True,
                verbose_name="请假率",
            ),
        ),
        migrations.AddField(
            model_name="performanceevaluation",
            name="rule_score",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="依据出勤/请假规则计算，0-100",
                max_digits=10,
                null=True,
                verbose_name="规则得分",
            ),
        ),
    ]
