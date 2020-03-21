from django.shortcuts import redirect
from django.views import View

from apps.fyle_connect.utils import FyleOAuth2

class AuthorizeFyleAccountView(View):
    """
    Authorize access to Fyle Account
    """
    def get(self, request):
        fyle_oauth = FyleOAuth2()
        return redirect(fyle_oauth.authorise('states'))
