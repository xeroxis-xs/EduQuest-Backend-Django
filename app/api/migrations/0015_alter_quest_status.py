# Generated by Django 5.0.6 on 2024-08-15 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_alter_term_end_date_alter_term_start_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quest',
            name='status',
            field=models.CharField(default='Active', max_length=50),
        ),
    ]