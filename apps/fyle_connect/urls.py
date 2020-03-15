from django.urls import path

from . import views

urlpatterns = [
    path('authorize/', views.AuthorizeFyleAccount.as_view(), name='connect-authorize'),

]