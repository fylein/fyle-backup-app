import json
import logging
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError

from apps.fyle_connect.utils import FyleOAuth2
from apps.user.models import UserProfile
from apps.backups.forms import ExpenseForm
from apps.data_fetcher.utils import notify_user, FyleSdkConnector
from .utils import FyleJobsSDK, BackupFilters
from .models import Backups, ObjectLookup

from fyle_backup_app import settings

logger = logging.getLogger('app')


@method_decorator(login_required, name='dispatch')
class HomeView(View):
    """
    User redirect post login
    """
    def get(self, request):
        # Prompt the user to connect to fyle if needed
        if request.user.refresh_token is None:
            return redirect('/fyle/')
        return redirect('/main/expenses/')

@method_decorator(login_required, name='dispatch')
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


@method_decorator(login_required, name='dispatch')
class BackupsView(View):
    """
    Insert/Get objects from backups table
    """
    def get(self, request, object_type=None):
        if object_type is None:
            return {'backups': None}
        backups_list = Backups.objects.filter(object_type_id__name=object_type,
                                              fyle_refresh_token=request.user.refresh_token
                                             ).values('id', 'name',
                                                      'current_state',
                                                      'error_message', 'created_at')[:5]
        return JsonResponse({"backups": list(backups_list)})

    def post(self, request):
        try:
            form = ExpenseForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                refresh_token = request.user.refresh_token
                fyle_org_id = request.user.fyle_org_id
                object_type = data.get('object_type')
                current_state = 'ONGOING'
                name = data.get('name').replace(' ', '')
                bkp_filter_obj = BackupFilters(data, object_type)
                filters = bkp_filter_obj.get_filters_for_object()
                data_format = data.get('data_format')
                object_type_obj = ObjectLookup.objects.get(name=object_type)
                backup = Backups.objects.create(name=name, current_state=current_state,
                                                object_type=object_type_obj, filters=filters,
                                                data_format=data_format, fyle_org_id=fyle_org_id,
                                                fyle_refresh_token=refresh_token
                                                )

                # Schedule this backup using JobsInfra
                fyle_sdk_connector = FyleSdkConnector(refresh_token)
                fyle_sdk_connection = fyle_sdk_connector.connection
                jobs = FyleJobsSDK(fyle_sdk_connection)
                created_job = jobs.trigger_now(
                    callback_url='{0}{1}'.format(settings.FYLE_JOBS_CALLBACK_URL,
                                                 '{0}/'.format(object_type)),
                    callback_method='POST',
                    object_id=backup.id,
                    payload={'backup_id': backup.id},
                    job_description='Fetch backup_id {0} for user: {1}'.format(
                        backup.id, self.request.user
                    ))
                if created_job is None:
                    logger.error('Backup_id: %s not scheduled. Task creation failed.', backup.id)
                    backup.current_state = 'FAILED'
                    backup.save()
                    messages.error(request, 'Something went wrong. Please try again!')
                    return redirect('/main/{0}/'.format(object_type))
                backup.task_id = created_job['id']
                backup.save()
                messages.success(request, 'Your backup request has been submitted. \
                             Once the file is generated we will send you the download\
                             link on the registered email id.')
                return redirect('/main/{0}/'.format(object_type))
            raise ValidationError(('Form data is invalid'), code='invalid')

        except (NotImplementedError, ValidationError) as excp:
            logger.error('Error during backup creation for backup: %s . Error: %s',
                         name, excp)
            messages.error(request, 'Something went wrong. Please try again!')
            return redirect('/main/{0}/'.format(object_type))


@method_decorator(login_required, name='dispatch')
class BackupsNotifyView(View):
    """
    Send backup download link to user via email
    """
    def get(self, request, backup_id):
        try:
            refresh_token = request.user.refresh_token
            backup = Backups.objects.get(id=backup_id, fyle_refresh_token=refresh_token)
            fyle_connection = FyleSdkConnector(refresh_token)
            notify_user(fyle_connection, backup.file_path, backup.fyle_org_id,
                        backup.object_type)
            messages.success(request, 'We have sent you the download\
                             link by email.')
        except Backups.DoesNotExist:
            messages.error(request, 'You are not authorized to do that!')
        except Exception as excp:
            logger.error('Error while notifying user for backup_id: %s. Error: %s',
                         backup_id, excp)
            messages.error(request, 'Something went wrong. Please try again!')
        return redirect('/main/{0}/'.format(backup.object_type))


@method_decorator(login_required, name='dispatch')
class ExpensesView(View):
    """
    Home view for Expenses
    """
    object_type = 'expenses'
    def get(self, request):
        if request.user.refresh_token is None:
            messages.error(request, 'Please connect your Fyle account!')
            return redirect('/fyle/')
        bkp_view = BackupsView()
        response = bkp_view.get(request, self.object_type)
        response = json.loads(response.content).get('backups')
        form = ExpenseForm()
        return render(request, 'expenses.html', {'form': form, 'backup_list':response,
                                                 'object_name': 'Expense',
                                                 'expenses_tab': 'active'})
