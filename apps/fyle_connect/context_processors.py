from apps.data_fetcher.utils import FyleSdkConnector

def org_name(request):
    """
    Context processor for Settings tab
    :param request:
    :return: organisation name for current active fyle account
    """
    if request.user.is_authenticated:
        try:
            fyle_sdk_connector = FyleSdkConnector(request.user.refresh_token)
            fyle_org_name = fyle_sdk_connector.extract_employee_details().get('org_name')
            return {'current_org_name': fyle_org_name, 'connected': True}
        except Exception:
            return {}
    return {}
