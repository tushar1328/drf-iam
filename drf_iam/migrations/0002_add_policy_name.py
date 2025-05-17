from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drf_iam", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="policy",
            name="policy_name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
