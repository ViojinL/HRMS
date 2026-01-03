from datetime import date

from django.test import TestCase
from django.utils import timezone

from apps.employee.models import Employee
from apps.organization.models import Organization


class EmployeeModelTests(TestCase):
    def setUp(self) -> None:
        self.org = Organization.objects.create(
            org_code="TEST-ORG-EMP",
            org_name="Test Org Employee",
            org_type="company",
            effective_time=timezone.now(),
            status="enabled",
            create_by="tests",
            update_by="tests",
        )

    def test_create_employee_and_str(self) -> None:
        emp = Employee.objects.create(
            emp_id="E001",
            id_card="123456789012345678",
            emp_name="John Doe",
            gender="male",
            birth_date=date(1990, 1, 1),
            phone="1234567890",
            email="john@example.com",
            hire_date=date(2020, 1, 1),
            org=self.org,
            position="Dev",
            employment_type="full_time",
            emp_status="active",
            create_by="tests",
            update_by="tests",
        )
        self.assertEqual(emp.emp_name, "John Doe")
        self.assertEqual(str(emp), "John Doe (E001)")
