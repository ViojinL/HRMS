from django.test import TestCase
from django.utils import timezone
from apps.organization.models import Organization
from apps.employee.models import Employee
from datetime import date


class EmployeeModelTests(TestCase):
    def test_create_employee(self):
        org = Organization.objects.create(
            org_code="TEST-ORG-EMP",
            org_name="Test Org Employee",
            org_type="company",
            effective_time=timezone.now(),
            status="enabled",
            create_by="test",
            update_by="test",
        )
        emp = Employee.objects.create(
            emp_id="E001",
            id_card="123456789012345678",
            emp_name="John Doe",
            gender="male",
            birth_date=date(1990, 1, 1),
            phone="1234567890",
            email="john@example.com",
            hire_date=date(2020, 1, 1),
            org=org,
            position="Dev",
            employment_type="full_time",
            emp_status="active",
            create_by="test",
            update_by="test",
        )
        self.assertEqual(emp.emp_name, "John Doe")
        self.assertEqual(str(emp), "John Doe (E001)")
