from django.shortcuts import render, redirect
from django.views import View

from apps.fyle_connect.utils import FyleOAuth2
from apps.user.models import UserProfile

class HomeView(View):
    """
    User redirect post login
    """
    def get(self, request):
        user = UserProfile.objects.values('refresh_token').get(email=request.user)
        # On first ever user login, we fetch fyle refresh token
        # and update this in the user model
        if user.get('refresh_token') is None:
            return redirect('/fyle/authorize/')
        return redirect('/main/expenses/')

class OAuthCallbackView(View):
    """
    Callback view for Fyle Oauth
    """
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        # user_id = request.GET.get('state')
        if code and error is None:
            fyle_oauth = FyleOAuth2()
            refresh_token = fyle_oauth.get_refresh_token(code)
            # Update user object with refresh token
            try:
                user = UserProfile.objects.get(email=request.user)
                user.refresh_token = refresh_token
                user.save()
                return redirect('/main/expenses/')
            except UserProfile.DoesNotExist:
                # TODO : logger
                print("Does Not Exist")
        # TODO: Display errors if any
        return redirect('/accounts/login/')

class ExpensesView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return render(request, 'expenses.html')
        return redirect('/accounts/login/')
