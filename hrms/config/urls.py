from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views


class CustomLoginView(auth_views.LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="password_change.html", success_url="/password_change/done/"
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="password_change_done.html"
        ),
        name="password_change_done",
    ),
    path("leave/", include("apps.leave.urls")),
    path("performance/", include("apps.performance.urls")),
    path("organization/", include("apps.organization.urls")),
    path("employee/", include("apps.employee.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("audit/", include("apps.audit.urls")),
    path("config/", include("apps.config.urls")),
    path("", include("apps.core.urls")),  # 将根路径交给 core app 处理
]
