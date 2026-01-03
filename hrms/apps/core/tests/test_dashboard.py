from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.employee.models import Employee
from apps.organization.models import Organization


class DashboardViewTests(TestCase):
    def setUp(self) -> None:
        self.dashboard_url = reverse("core:dashboard")

    def _create_org(self, code: str = "ORG-001", name: str = "测试组织") -> Organization:
        return Organization.objects.create(
            org_code=code,
            org_name=name,
            org_type="company",
            effective_time=timezone.now(),
            status="enabled",
            create_by="tests",
            update_by="tests",
        )

    def _create_employee(
        self, user: User, org: Organization, emp_id: str = "E1001"
    ) -> Employee:
        return Employee.objects.create(
            emp_id=emp_id,
            id_card=f"4201231990{emp_id.zfill(6)}",
            emp_name="测试员工",
            gender="male",
            birth_date=timezone.now().date(),
            phone="13800000000",
            email=f"{emp_id.lower()}@example.com",
            hire_date=timezone.now().date(),
            org=org,
            position="工程师",
            employment_type="full_time",
            emp_status="active",
            user=user,
            create_by="tests",
            update_by="tests",
        )

    def test_anonymous_redirects_to_login(self) -> None:
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_superuser_sees_admin_dashboard(self) -> None:
        admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Password123!",
        )
        self.client.force_login(admin_user)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_admin_dashboard"])
        self.assertIn("total_employees", response.context)
        self.assertIn("total_orgs", response.context)
        self.assertIn("active_users", response.context)

    def test_employee_dashboard_shows_user_display_name(self) -> None:
        user = User.objects.create_user(
            username="bob", email="bob@example.com", password="Password123!"
        )
        org = self._create_org()
        employee = self._create_employee(user=user, org=org)
        self.client.force_login(user)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user_display_name"], employee.emp_name)
        self.assertIn("recent_leaves", response.context)
        self.assertIn("pending_approvals_count", response.context)
