# Generated by Django 5.0.6 on 2024-08-05 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_document_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
