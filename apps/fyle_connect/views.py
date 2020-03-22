from django.shortcuts import redirect, render
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from apps.fyle_connect.utils import FyleOAuth2
from apps.user.models import UserProfile

@method_decorator(login_required, name='dispatch')
class SourceView(View):
    """
    Fyle (source) connect view
    """
    template_name = "fyle_connect/source.html"

    def get(self, request):
        connected = True
        if request.user.refresh_token is None:
            connected = False
        context = {"source": "active", "connected": connected,
                   "settings_tab": "active"}
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
class FyleConnectView(View):
    """
    Authorize access to Fyle Account
    """
    def post(self, request):
        fyle_oauth = FyleOAuth2()
        return redirect(fyle_oauth.authorise('states'))

@method_decorator(login_required, name='dispatch')
class FyleDisconnectView(View):
    """
    Authorize access to Fyle Account
    """
    def post(self, request):
        user = UserProfile.objects.get(email=request.user)
        user.refresh_token = None
        user.save()
        return HttpResponseRedirect(reverse('fyle-source'))
