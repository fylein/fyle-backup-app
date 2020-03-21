from django.urls import path

from . import views

urlpatterns = [
    path('authorize/', views.AuthorizeFyleAccountView.as_view(), name='connect-authorize'),

]