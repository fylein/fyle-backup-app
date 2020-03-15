from django.urls import path

from . import views

urlpatterns = [
    path('home/', views.HomeView.as_view(), name='backups-home'),
    path('callback/', views.OAuthCallbackView.as_view(), name='backups-callback'),
    path('expenses/', views.ExpensesView.as_view(), name='backups-expenses'),

]