from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):
    def setUp(self) -> None:
        self.login_url = reverse("login")
        self.dashboard_url = reverse("core:dashboard")
        self.user = User.objects.create_user(
            username="alice", password="Password123!"
        )

    def test_login_page_renders(self) -> None:
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_login_success_redirects_dashboard(self) -> None:
        response = self.client.post(
            self.login_url,
            {"username": "alice", "password": "Password123!"},
        )
        self.assertRedirects(
            response,
            self.dashboard_url,
            fetch_redirect_response=False,
        )

    def test_authenticated_user_is_redirected(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertRedirects(
            response,
            self.dashboard_url,
            fetch_redirect_response=False,
        )
