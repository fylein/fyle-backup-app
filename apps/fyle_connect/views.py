from django.shortcuts import redirect, render
from django.views import View

from apps.fyle_connect.utils import FyleOAuth2
from apps.user.models import UserProfile


class SourceView(View):
    """
    Fyle (source) connect view
    """
    template_name = "fyle_connect/source.html"

    def get(self, request):
        context = {"source": "active", "settings_tab": "active"}
        return render(request, self.template_name, context)


class FyleConnectView(View):
    """
    Authorize access to Fyle Account
    """

    def get(self, request):
        fyle_oauth = FyleOAuth2()
        return redirect(fyle_oauth.authorize('states'))


class FyleDisconnectView(View):
    """
    Authorize access to Fyle Account
    """

    def post(self, request):
        user = UserProfile.objects.get(email=request.user)
        user.refresh_token = None
        user.fyle_org_id = None
        user.save()
        return redirect('/fyle/connect/')
