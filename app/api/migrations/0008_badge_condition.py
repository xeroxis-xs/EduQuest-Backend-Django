# Generated by Django 5.0.6 on 2024-07-30 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_rename_expired_on_quest_expiration_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='badge',
            name='condition',
            field=models.CharField(default='this is condition 1, this is another condition, and this is the last condition', max_length=250),
            preserve_default=False,
        ),
    ]
