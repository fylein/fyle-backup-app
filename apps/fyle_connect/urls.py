from django.urls import path

from apps.fyle_connect.views import SourceView, FyleConnectView, FyleDisconnectView

urlpatterns = [
    path('', SourceView.as_view(), name="fyle-source"),
    path('connect/', FyleConnectView.as_view(), name='fyle-connect'),
    path('disconnect/', FyleDisconnectView.as_view(), name='fyle-disconnect'),
]