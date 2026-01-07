from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):
    def setUp(self) -> None:
        self.login_url = reverse("login")
        self.dashboard_url = reverse("core:dashboard")
        self.user = User.objects.create_user(username="alice", password="Password123!")

    def test_login_page_renders(self) -> None:
        print("\n[功能验证] 检查登录页面加载状态...")
        response = self.client.get(self.login_url)
        print(f"[响应状态] HTTP {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        print("[校验通过] 登录页面渲染正常。")

    def test_login_success_redirects_dashboard(self) -> None:
        print("\n[安全验证] 模拟合法凭证登录过程...")
        print(f"[请求信息] 用户名: alice, 目标跳转: {self.dashboard_url}")
        response = self.client.post(
            self.login_url,
            {"username": "alice", "password": "Password123!"},
        )
        print(f"[响应状态] HTTP {response.status_code}, 重定向至: {response.url}")
        self.assertRedirects(
            response,
            self.dashboard_url,
            fetch_redirect_response=False,
        )
        print("[校验通过] 成功登录并正确跳转。")

    def test_authenticated_user_is_redirected(self) -> None:
        print("\n[流程验证] 已登录用户访问登录页面的自动拦截...")
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        print(f"[重定向路径] {response.url}")
        self.assertRedirects(
            response,
            self.dashboard_url,
            fetch_redirect_response=False,
        )
        print("[校验通过] 已登录用户被正确拦截并回正至仪表盘。")
