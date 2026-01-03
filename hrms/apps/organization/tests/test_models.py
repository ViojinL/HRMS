from django.test import TestCase
from django.utils import timezone

from apps.employee.models import Employee
from apps.organization.models import Organization


class OrganizationModelTests(TestCase):
    def setUp(self) -> None:
        self.parent = Organization.objects.create(
            org_code="ORG-PARENT",
            org_name="母组织",
            org_type="company",
            effective_time=timezone.now(),
            status="enabled",
            create_by="tests",
            update_by="tests",
        )
        self.manager = Employee.objects.create(
            emp_id="M001",
            id_card="420123199001010000",
            emp_name="负责人",
            gender="male",
            birth_date=timezone.now().date(),
            phone="13800000001",
            email="manager@example.com",
            hire_date=timezone.now().date(),
            org=self.parent,
            position="负责人",
            employment_type="full_time",
            emp_status="active",
            create_by="tests",
            update_by="tests",
        )

    def test_str_and_parent_relationship(self) -> None:
        child = Organization.objects.create(
            org_code="ORG-CHILD",
            org_name="子组织",
            org_type="department",
            parent_org=self.parent,
            manager_emp=self.manager,
            effective_time=timezone.now(),
            status="enabled",
            create_by="tests",
            update_by="tests",
        )
        self.assertEqual(str(child), "子组织 (ORG-CHILD)")
        self.assertEqual(child.parent_org, self.parent)
        self.assertEqual(child.manager_emp, self.manager)
