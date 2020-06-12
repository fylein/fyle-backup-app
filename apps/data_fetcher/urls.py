from django.urls import path

from . import views

urlpatterns = [
    path('callback/expenses/', views.ExpensesFetchView.as_view(), name='fetcher-expenses'),
]
