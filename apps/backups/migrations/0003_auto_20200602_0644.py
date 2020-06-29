# Generated by Django 3.0.4 on 2020-06-02 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backups', '0002_backups_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='backups',
            name='fyle_file_id',
            field=models.CharField(
                default='', help_text='File ID of file', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='backups',
            name='error_message',
            field=models.TextField(
                help_text='Backup failure reason', null=True),
        ),
        migrations.AlterField(
            model_name='backups',
            name='file_path',
            field=models.TextField(
                help_text='Cloud storage URL for this backup', null=True),
        ),
        migrations.AlterField(
            model_name='backups',
            name='fyle_refresh_token',
            field=models.TextField(help_text='Fyle Refresh Token'),
        ),
    ]
