from django.urls import path
from . import views

app_name = "performance"

urlpatterns = [
    path("", views.PerformanceDashboardView.as_view(), name="dashboard"),
    path("cycle/add/", views.PerformanceCycleCreateView.as_view(), name="cycle_add"),
    path(
        "cycle/<str:pk>/delete/",
        views.PerformanceCycleDeleteView.as_view(),
        name="cycle_delete",
    ),
    path(
        "cycle/<str:pk>/status/",
        views.PerformanceCycleStatusUpdateView.as_view(),
        name="cycle_status",
    ),
    path("my/", views.MyEvaluationListView.as_view(), name="my_list"),
    path(
        "manage/",
        views.PerformanceEvaluationManageListView.as_view(),
        name="manage_list",
    ),
    path(
        "manage/<str:pk>/",
        views.PerformanceEvaluationManageUpdateView.as_view(),
        name="manage_edit",
    ),
    path("search/", views.PerformanceSearchView.as_view(), name="search"),
]
