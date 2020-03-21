import json
import requests
from fyle_backup_app import settings

class BackupFilter():
    """
    Fetch filter values based on business object
    """
    def __init__(self, request, object_type):
        self.request = request
        self.object_type = object_type

    def get_filters_for_object(self):
        """
        Get filters and their values based on business object
        """
        if self.object_type == 'expenses':
            return get_expenses_filters(self.request)
        raise NotImplementedError

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


def get_filters_for_object(request, object_type):
    """
    Get filters and their values based on business object
    """
    if object_type == 'expenses':
        return get_expenses_filters(request)

def get_expenses_filters(request):
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
    filters = json.dumps({"state": state, "approved_at": approved_at,
                          "updated_at": updated_at, "download_attachments":download_attachments})
    return filters


class FyleJobsSDK:
    """
    Fyle Jobs SDK
    """

    def __init__(self, fyle_sdk_connection):
        self.user_profile = fyle_sdk_connection.Employees.get_my_profile()['data']
        self.access_token = fyle_sdk_connection.access_token

    def trigger_now(self, callback_url, callback_method,
                    job_description, object_id, payload):
        """
        Trigger callback immediately
        :param payload: callback payload
        :param callback_url: callback URL for the job
        :param callback_method: HTTP method for callback
        :param job_description: Job description
        :param object_id: object id
        :returns: response
        """
        body = {
            'template': {
                'name': 'http.main',
                'data': {
                    'url': callback_url,
                    'method': callback_method,
                    'payload': payload
                }
            },
            'job_data': {
                'description': job_description,
            },
            'job_meta_data': {
                'object_id': object_id
            },
            'notification': {
                'enabled': False
            },
            'org_user_id': self.user_profile['id']
        }

        api_headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer {0}'.format(self.access_token)
        }

        response = requests.post(
            settings.FYLE_JOBS_URL,
            headers=api_headers,
            json=body
        )
        print('response of jobs hit')
        print(response)

        if response.status_code == 200:
            result = json.loads(response.text)
            return result
        return None
