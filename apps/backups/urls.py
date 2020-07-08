from django.urls import path

from . import views

urlpatterns = [
    path('home/', views.HomeView.as_view(), name='backups-home'),
    path('callback/', views.OAuthCallbackView.as_view(), name='backups-callback'),
    path('expenses/', views.ExpensesListView.as_view(), name='backups-expenses-list'),
    path('expenses/create/', views.ExpensesCreateView.as_view(), name='backups-expenses-create'),
    path('backups/', views.BackupsView.as_view(), name='backups-backup'),
    path('backups/notify/<int:backup_id>/', views.BackupsNotifyView.as_view(),
         name='backups-notify')
]
