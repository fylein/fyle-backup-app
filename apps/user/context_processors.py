from allauth.socialaccount.models import SocialAccount

def user_data(request):
    """
    Context processor for Navbar
    :param request:
    :return: username and organisation name
    """
    if request.user.is_authenticated:
        try:
            user_details = SocialAccount.objects.get(user=request.user).extra_data['data']
            return {'username': user_details.get('full_name'), 'org': user_details.get('org_name')}
        except SocialAccount.DoesNotExist:
            return {}
    return {}
