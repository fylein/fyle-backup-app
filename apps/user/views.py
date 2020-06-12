from django.shortcuts import render, redirect
from django.views import View


class UserLoginView(View):
    """
    View for user login
    """
    template_name = "user/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/main/expenses/')
        return render(request, self.template_name)
