from django.urls import path
from . import views

app_name = 'employee'

urlpatterns = [
    path('', views.EmployeeListView.as_view(), name='list'),
    path('sql-search/', views.EmployeeOrgSqlSearchView.as_view(), name='sql_search'),
    path('import/', views.EmployeeImportView.as_view(), name='import'),
    path('download-template/', views.EmployeeTemplateDownloadView.as_view(), name='download_template'),
    path('hr/onboarding/', views.HROnboardingView.as_view(), name='hr_onboarding'),
    path('add/', views.EmployeeCreateView.as_view(), name='add'),
    path('<str:pk>/edit/', views.EmployeeUpdateView.as_view(), name='edit'),
    path('<str:pk>/', views.EmployeeDetailView.as_view(), name='detail'),
]
