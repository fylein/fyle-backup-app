import json
import logging
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError

from apps.fyle_connect.utils import FyleOAuth2
from apps.user.models import UserProfile
from apps.backups.forms import ExpenseForm
from apps.data_fetcher.utils import notify_user, FyleSdkConnector
from fyle_backup_app import settings

from .utils import create_backup, schedule_backup
from .models import Backups, ObjectLookup

logger = logging.getLogger('app')


class HomeView(View):
    """
    User redirect post login
    """
    def get(self, request):
        # Update refresh_token and org_id of user model to
        # that of currently logged in org
        try:
            current_org = request.user.socialaccount_set.get(provider="fyle")
            user = UserProfile.objects.get(email=request.user)
            user.refresh_token = current_org.socialtoken_set.first().token_secret
            user.fyle_org_id = current_org.extra_data.get('data').get('org_id')
            user.save()
            return redirect('/main/expenses/')
        except Exception as excp:
            logger.error('Exception in main/home view. Error: %s', excp)
            return redirect('/')


class OAuthCallbackView(View):
    """
    Callback view for Fyle Oauth
    """
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        if code and error is None:
            fyle_oauth = FyleOAuth2()
            refresh_token = fyle_oauth.get_refresh_token(code)
            fyle_sdk_connector = FyleSdkConnector(refresh_token)
            fyle_org_id = fyle_sdk_connector.extract_employee_details().get('org_id')
            user = UserProfile.objects.get(email=request.user)
            user.refresh_token = refresh_token
            user.fyle_org_id = fyle_org_id
            user.save()
            return redirect('/main/expenses/')
        messages.error(request, 'Please Authorize Fyle Backup Application\
                       to access your Fyle Account.')
        return redirect('/')


class BackupsView(View):
    """
    Insert/Get objects from backups table
    """
    def get(self, request, object_type=None):
        if object_type is None:
            return {'backups': None}
        backups_list = Backups.objects.filter(object_type=ObjectLookup[object_type],
                                              user_id__email=request.user
                                             ).values('id', 'name', 'current_state',
                                                      'error_message',
                                                      'created_at')[:settings.BACKUPS_LIMIT]
        return JsonResponse({"backups": list(backups_list)})

    def post(self, request):
        try:
            form = ExpenseForm(request.POST)
            logger.info('Got a backup request from %s with params: %s',
                        request.user, request.POST)
            if not form.is_valid():
                raise ValidationError(('Form data is invalid'), code='invalid')

            data = form.cleaned_data
            object_type = data.get('object_type')
            backup = create_backup(request, data)
            created_job = schedule_backup(request, backup)
            if not created_job:
                messages.error(request, 'Something went wrong. Please try again!')
                return redirect('/main/{0}/'.format(object_type))

            messages.success(request, 'Your backup request has been submitted. \
                            Once the file is generated we will send you the download\
                            link on the registered email id.')
            return redirect('/main/{0}/'.format(object_type))

        except Exception as excp:
            logger.error('Error during backup creation for backup: %s. Error: %s',
                         request.POST.get('name'), excp)
            messages.error(request, 'Something went wrong. Please try again!')
            return redirect('/main/{0}/'.format(request.POST.get('object_type')))


class BackupsNotifyView(View):
    """
    Send backup download link to user via email
    """
    def get(self, request, backup_id):
        try:
            logger.info('Got a notify request from user %s for backup_id: %s',
                        request.user, backup_id)
            backup = Backups.objects.get(id=backup_id, user_id__email=request.user)
            fyle_connection = FyleSdkConnector(backup.fyle_refresh_token)
            object_type = ObjectLookup(backup.object_type).label.lower()
            notify_user(fyle_connection, backup.file_path, backup.fyle_org_id,
                        object_type)
            messages.success(request, 'We have sent you the download\
                             link by email.')
            return redirect('/main/{0}/'.format(object_type))
        except Backups.DoesNotExist:
            messages.error(request, 'Did not find a backup for this id.')
        except Exception as excp:
            logger.error('Error while notifying user for backup_id: %s. Error: %s',
                         backup_id, excp)
            messages.error(request, 'Something went wrong. Please try again!')
        return redirect('/main/expenses/')


class ExpensesView(View):
    """
    Home view for Expenses
    """
    object_type = 'expenses'
    def get(self, request):
        if request.user.refresh_token is None:
            messages.error(request, 'Please connect your Fyle account!')
            return redirect('/fyle/connect/')
        bkp_view = BackupsView()
        response = bkp_view.get(request, self.object_type)
        response = json.loads(response.content).get('backups')
        form = ExpenseForm()
        return render(request, 'expenses.html', {'form': form, 'backup_list':response,
                                                 'object_name': 'Expense',
                                                 'expenses_tab': 'active'})
