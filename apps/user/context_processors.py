from apps.data_fetcher.utils import FyleSdkConnector


def user_data(request):
    """
    Context processor for Navbar
    :param request:
    :return: username and organisation name
    """
    if request.user.is_authenticated:
        try:
            fyle_sdk_connector = FyleSdkConnector(request.user.refresh_token)
            user_details = fyle_sdk_connector.extract_employee_details()
            return {
                'username': user_details.get('full_name'),
                'org': user_details.get('org_name')}
        except Exception:
            return {}
    return {}
