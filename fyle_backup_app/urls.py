"""fyle_backup_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from decorator_include import decorator_include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include


from apps.user.views import UserLoginView
from apps.backups.views import BackupsUpdateAttachments

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', UserLoginView.as_view(), name='User login'),
    path('backups/attachments/', BackupsUpdateAttachments.as_view(),
         name='backups-attachments'),
    path('accounts/social/login/cancelled/', UserLoginView.as_view()),
    path('accounts/', include('allauth.urls')),
    path('main/', decorator_include([login_required], 'apps.backups.urls')),
    path('fyle/', decorator_include([login_required], 'apps.fyle_connect.urls')),
    path('fetcher/', include('apps.data_fetcher.urls'))
]
