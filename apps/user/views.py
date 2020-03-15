from django.shortcuts import redirect
from django.views import View


class UserLoginView(View):
    """
    View for user login
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/main/home/')
        return redirect('/accounts/login/')
