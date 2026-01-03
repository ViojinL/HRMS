from django.urls import path

from .views import ConfigHomeView

app_name = "config"

urlpatterns = [
    path("", ConfigHomeView.as_view(), name="dashboard"),
]
