# Generated by Django 5.0.6 on 2024-09-13 09:25

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_rename_from_course_group_quest_course_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercoursegroupenrollment',
            name='students',
            field=models.ManyToManyField(related_name='enrolled_course_groups', to=settings.AUTH_USER_MODEL),
        ),
    ]