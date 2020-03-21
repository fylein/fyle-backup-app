from .models import UserProfile
def user_data(request):
    """
    Context processor for Navbar
    :param request:
    :return: user email
    """
    if request.user.is_authenticated:
        print(request.user.email)
        try:
            # Extend this to return org name, and user name later
            # user_details = UserProfile.objects.get(email=request.user)
            return {'username': request.user.email}
        except UserProfile.DoesNotExist:
            return {}
    return {}
