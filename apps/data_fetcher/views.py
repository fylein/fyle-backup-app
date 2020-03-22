import logging
import json

from django.views import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from fyle_backup_app import settings
from apps.backups.models import Backups

from .utils import FyleSdkConnector, CloudStorage, Dumper, notify_user, remove_items_from_tmp
logger = logging.getLogger('app')


# Authentication for this view to be taken up in v2.
@method_decorator(csrf_exempt, name='dispatch')
class ExpensesFetchView(View):
    """
    Prepare backup data and upload to S3
    """
    path = settings.DOWNLOAD_PATH
    def post(self, request):
        logger.info('Got callback hit from Jobs Infra with params: %s', request.body)
        backup_id = json.loads(request.body).get('backup_id')
        try:
            backup = Backups.objects.get(id=backup_id)
        except Backups.DoesNotExist:
            logger.error('Invalid backup_id sent by JobsInfra. Request: %s', request.POST)
            return HttpResponse(status=400)

        filters = json.loads(backup.filters)
        download_attachments = filters.get('download_attachments')
        refresh_token = backup.fyle_refresh_token
        fyle_org_id = backup.fyle_org_id
        name = backup.name
        # Fetch expenses matching the filters and dump into a local file
        try:
            fyle_connection = FyleSdkConnector(refresh_token)
        except Exception as e:
            logger.error('Could not get a connection through FyleSDKConnector for %s. Error: %s',
                         backup_id, e)
            return HttpResponse(status=500)
        response_data = fyle_connection.extract_expenses(state=filters.get('state'),
                                                         approved_at=filters.get('approved_at'),
                                                         updated_at=filters.get('updated_at'))
        if not response_data:
            logger.info('No data found for backup_id: %s', backup_id)
            backup.current_state = 'NO_DATA_FOUND'
            backup.save()
            return HttpResponse(status=200)
        dumper = Dumper(fyle_connection, path=self.path, data=response_data, name=name,
                        fyle_org_id=fyle_org_id, download_attachments=download_attachments)
        try:
            file_path = dumper.dump_data()
            logger.info('Download Successful for backup_id: %s', backup_id)

            cloud_store = CloudStorage()
            cloud_store.upload(file_path, fyle_org_id)
            logger.info('Cloud upload Successful for backup_id: %s', backup_id)
            # Get only the object name for db save
            object_name = file_path.split('/')[2]

            # Get a secure URL for this backup and mail it to user
            notify_user(fyle_connection, object_name, fyle_org_id, 'expenes')

            backup.file_path = object_name
            backup.current_state = 'READY'
            backup.save()
            # Remove the files from local machine
            remove_items_from_tmp(file_path)
            return HttpResponse(status=200)
        except Exception as e:
            backup.current_state = 'FAILED'
            backup.save()
            logger.error('Backup process failed for bkp_id: %s . Error: %s', backup_id, e)
            return HttpResponse(status=500)
