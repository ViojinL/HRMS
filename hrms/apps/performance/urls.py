from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    path('', views.PerformanceDashboardView.as_view(), name='dashboard'),
    path('cycle/add/', views.PerformanceCycleCreateView.as_view(), name='cycle_add'),
    path('my/', views.MyEvaluationListView.as_view(), name='my_list'),
    path('my/<str:pk>/', views.DoSelfEvaluationView.as_view(), name='do_self_eval'),
    path('team/', views.TeamEvaluationListView.as_view(), name='team_list'),
    path('team/<str:pk>/', views.DoManagerEvaluationView.as_view(), name='do_manager_eval'),
]
