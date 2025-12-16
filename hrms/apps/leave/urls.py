from django.urls import path
from . import views

app_name = 'leave'

urlpatterns = [
    path('', views.LeaveListView.as_view(), name='list'),
    path('apply/', views.LeaveApplyView.as_view(), name='apply'),
    path('approvals/', views.LeaveApprovalListView.as_view(), name='approval_list'),
    path('<str:pk>/', views.LeaveDetailView.as_view(), name='detail'),
    path('<str:pk>/action/', views.LeaveActionView.as_view(), name='action'),
]
