import logging

from django.views import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from fyle_backup_app import settings
from apps.backups.models import Backups

from .utils import FyleSdkConnector, CloudStorage, Dumper, notify_user
logger = logging.getLogger('app')

# Authentication for this view to be taken up in v2.
@method_decorator(csrf_exempt, name='dispatch')
class ExpensesFetchView(View):
    """
    Prepare backup data and upload to S3
    """
    path = settings.DOWNLOAD_PATH
    def post(self, request):
        logger.info('Got callback hit from Jobs Infra with params: %s', request.POST)
        backup_id = request.POST.get('backup_id')
        try:
            backup = Backups.objects.get(id=backup_id)
        except Backups.DoesNotExist:
            logger.error('Invalid backup_id sent by JobsInfra. Request: %s', request.POST)
            return HttpResponse(status=400)
        filters = {}
        #json.loads(backup.filters)
        download_attachments = 'True'#filters.get('download_attachments', False)
        refresh_token = backup.fyle_refresh_token
        fyle_org_id = 'ormsDa8NCYdL' #backup.fyle_org_id
        name = backup.name

        # Fetch expenses matching the filters and dump into a local file
        fyle_connection = FyleSdkConnector(refresh_token)
        response_data = fyle_connection.extract_expenses(state=filters.get('state'),
                                                         approved_at=filters.get('approved_at'),
                                                         updated_at=filters.get('updated_at'))
        dumper = Dumper(fyle_connection, path=self.path, data=response_data, name=name,
                        fyle_org_id=fyle_org_id, download_attachments=download_attachments)
        try:
            file_path = dumper.dump_data()
            logger.info('Download Successful for backup_id: %s', backup_id)

            # Upload the local data file to Clourd storage
            cloud_store = CloudStorage()
            cloud_store.upload(file_path, fyle_org_id)
            logger.info('Cloud upload Successful for backup_id: %s', backup_id)

            # store file_path in db

            # Get a secure URL for this backup and mail it to user
            url = notify_user(fyle_connection, file_path, fyle_org_id)
            logger.info(url)
            # Update current state: READY
            return HttpResponse(status=200)
        except Exception as e:
            # Update current_state : FAILED
            return HttpResponse(status=500)
