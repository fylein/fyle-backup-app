# Generated by Django 3.0.4 on 2020-06-03 06:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backups', '0003_auto_20200602_0644'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='backups',
            name='file_path',
        ),
    ]
