# Generated by Django 5.0.6 on 2024-08-05 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_answer_reason'),
    ]

    operations = [
        migrations.AlterField(
            model_name='term',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='term',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
