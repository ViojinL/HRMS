from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.AttendanceDashboardView.as_view(), name='dashboard'),
]
