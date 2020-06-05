import json
import logging
import traceback
import requests
from apps.user.models import UserProfile
from apps.data_fetcher.utils import FyleSdkConnector
from fyle_backup_app import settings

from .models import Backups, ObjectLookup
logger = logging.getLogger('app')

class BackupFilters():
    """
    Fetch filter values based on business object
    """
    def __init__(self, request, object_type):
        self.request = request
        self.object_type = object_type

    def get_expenses_filters(self):
        """
        Fetch values of filters for the Expense object
        """
        request = self.request
        state = request.get('state')
        approved_at = []
        approved_at_gte = request.get('approved_at_gte')
        approved_at_lte = request.get('approved_at_lte')
        if approved_at_gte:
            approved_at.append("gte:{0}{1}".format(approved_at_gte, 'T00:00:00.000Z'))
        if approved_at_lte:
            approved_at.append("lte:{0}{1}".format(approved_at_lte, 'T23:59:59.000Z'))

        updated_at = []
        updated_at_gte = request.get('updated_at_gte')
        updated_at_lte = request.get('updated_at_lte')
        if updated_at_gte:
            updated_at.append("gte:{0}{1}".format(updated_at_gte, 'T00:00:00.000Z'))
        if updated_at_lte:
            updated_at.append("lte:{0}{1}".format(updated_at_lte, 'T23:59:59.000Z'))
        download_attachments = request.get('download_attachments')
        filter_value_dict = json.dumps({"state": state, "approved_at": approved_at,
                                        "updated_at": updated_at,
                                        "download_attachments":download_attachments})
        return filter_value_dict

    def get_filters_for_object(self):
        """
        Get filters and their values based on business object
        """
        if self.object_type == 'expenses':
            return self.get_expenses_filters()
        raise NotImplementedError


def create_backup(request, data):
    """
    Create a new backup
    :param request: The request object
    :param data: cleaned form data
    """
    refresh_token = request.user.refresh_token
    fyle_org_id = request.user.fyle_org_id
    object_type = data.get('object_type')
    current_state = 'ONGOING'
    name = data.get('name')
    try:
        bkp_filter_obj = BackupFilters(data, object_type)
    except NotImplementedError:
        raise
    filters = bkp_filter_obj.get_filters_for_object()
    data_format = data.get('data_format')
    user = UserProfile.objects.get(email=request.user)
    backup = Backups.objects.create(name=name, current_state=current_state,
                                    object_type=ObjectLookup[object_type],
                                    filters=filters, data_format=data_format,
                                    fyle_org_id=fyle_org_id, user=user,
                                    fyle_refresh_token=refresh_token
                                    )
    return backup

def schedule_backup(request, backup):
    """
    Schedule this backup using JobsInfra
    :param request: request object
    :param backup: backup object
    """
    try:
        fyle_sdk_connector = FyleSdkConnector(request.user.refresh_token)
        fyle_sdk_connection = fyle_sdk_connector.connection
        jobs = fyle_sdk_connection.Jobs
        org_user_id = fyle_sdk_connection.Employees.get_my_profile()['data']['id']
        object_type = request.POST.get('object_type')
        created_job = jobs.trigger_now(
            callback_url='{0}{1}/'.format(settings.FYLE_JOBS_CALLBACK_URL,
                                          object_type),
            callback_method='POST',
            org_user_id=org_user_id,
            job_description='Fetch backup_id {0} for user: {1}'.format(
                backup.id, request.user
            ),
            object_id=backup.id,
            payload={'backup_id': backup.id}
        )
        backup.task_id = created_job['id']
        backup.save()
        return True
    except Exception as excp:
        error = traceback.format_exc()
        logger.error('Exception occured while scheduling backup_id: %s, Traceback: ', backup.id, error)
