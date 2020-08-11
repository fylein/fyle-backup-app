import logging
import json

from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.backups.models import Backups

from .utils import fetch_and_notify_expenses
logger = logging.getLogger('app')


# Authentication for this view to be taken up in v2.
@method_decorator(csrf_exempt, name='dispatch')
class ExpensesFetchView(View):
    """
    Prepare backup data, upload to cloud, notify user
    """

    def post(self, request):
        logger.info(
            'Got callback hit from Jobs Infra with params: %s', request.body)
        backup_id = json.loads(request.body).get('backup_id')
        try:
            backup = Backups.objects.get(id=backup_id)
        except Backups.DoesNotExist:
            logger.error(
                'Invalid backup_id sent by JobsInfra. Request: %s',
                request.POST)
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid backup_id.'}, status=400)

        is_sucess = fetch_and_notify_expenses(backup)
        if is_sucess:
            return JsonResponse(
                {'status': 'success', 'message': 'Backup processed.'}, status=200)

        return JsonResponse({'status': 'error', 'message': 'Backup failed.'},
                            status=500)
