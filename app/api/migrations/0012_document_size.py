# Generated by Django 5.0.6 on 2024-08-05 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_document_uploaded_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='size',
            field=models.FloatField(default=1.0),
            preserve_default=False,
        ),
    ]
