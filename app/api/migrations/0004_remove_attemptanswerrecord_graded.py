# Generated by Django 5.0.6 on 2024-07-12 10:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_remove_attemptanswerrecord_is_correct'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attemptanswerrecord',
            name='graded',
        ),
    ]
