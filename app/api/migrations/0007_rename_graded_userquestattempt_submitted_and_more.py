# Generated by Django 5.0.6 on 2024-07-17 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_alter_userquestquestionattempt_score_achieved'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userquestattempt',
            old_name='graded',
            new_name='submitted',
        ),
        migrations.AlterField(
            model_name='question',
            name='max_score',
            field=models.FloatField(default=1),
        ),
    ]
