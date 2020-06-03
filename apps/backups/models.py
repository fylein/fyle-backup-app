from django.db import models
from apps.user.models import UserProfile


class ObjectLookup(models.IntegerChoices):
    """
    Fyle's Business objects
    """
    expenses = 1


class Backups(models.Model):
    """
    Table to store user's backup request
    """
    id = models.AutoField(primary_key=True)
    fyle_org_id = models.CharField(max_length=255, help_text='Fyle org_id of backup requester')
    fyle_refresh_token = models.TextField(help_text='Fyle Refresh Token')
    user = models.ForeignKey(UserProfile, on_delete=models.PROTECT)
    object_type = models.IntegerField(choices=ObjectLookup.choices)
    current_state = models.CharField(max_length=64, help_text="Current state of backup")
    name = models.CharField(max_length=64, help_text="Backup name")
    task_id = models.CharField(max_length=255, null=True,
                               help_text='Task reference for Fyle Jobs Infra')
    filters = models.TextField(help_text='The backup configuration')
    data_format = models.CharField(max_length=10, help_text="Data format for backup")
    error_message = models.TextField(null=True, help_text="Backup failure reason")
    # we are now storing S3 object name in file_path
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    modified_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')
    fyle_file_id = models.CharField(max_length=255, help_text='File ID of file')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = "created_at"
