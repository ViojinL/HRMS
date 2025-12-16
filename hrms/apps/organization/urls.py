from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    path('tree/', views.OrganizationTreeView.as_view(), name='tree'),
    path('', views.OrganizationListView.as_view(), name='list'),
    path('add/', views.OrganizationCreateView.as_view(), name='add'),
    path('<str:pk>/edit/', views.OrganizationUpdateView.as_view(), name='edit'),
    path('<str:pk>/delete/', views.OrganizationDeleteView.as_view(), name='delete'),
]
