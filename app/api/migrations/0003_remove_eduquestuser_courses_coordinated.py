# Generated by Django 5.0.6 on 2024-09-12 23:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_eduquestuser_courses_coordinated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eduquestuser',
            name='courses_coordinated',
        ),
    ]