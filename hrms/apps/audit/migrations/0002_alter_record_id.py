from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="record_id",
            field=models.CharField(
                blank=True, max_length=200, null=True, verbose_name="记录ID/URL"
            ),
        ),
    ]
