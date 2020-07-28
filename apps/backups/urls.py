from django.urls import path

from . import views

urlpatterns = [
    path('home/', views.HomeView.as_view(), name='backups-home'),
    path('callback/', views.OAuthCallbackView.as_view(), name='backups-callback'),
    path('expenses/', views.ExpensesView.as_view(), name='backups-expenses'),
    path('backups/', views.BackupsView.as_view(), name='backups-backup'),
    path('backups/download/', views.DownloadsView.as_view(), name='backups-download'),
    path('backups/list/', views.BackupsJSONView.as_view(), name='backups-json'),
    path('backups/notify/<int:backup_id>/', views.BackupsNotifyView.as_view(),
         name='backups-notify'),
]
