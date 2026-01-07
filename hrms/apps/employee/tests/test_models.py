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
        print("\n[模型验证] 验证员工档案创建及字符串标识格式...")
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
        print(f"[数据录入] 员工姓名: {emp.emp_name}, 工号: {emp.emp_id}")
        self.assertEqual(emp.emp_name, "John Doe")
        
        print(f"[格式化验证] 期望格式: 'John Doe (E001)' -> 实际输出: '{str(emp)}'")
        self.assertEqual(str(emp), "John Doe (E001)")
        print("[校验通过] 员工档案模型及展示逻辑正常。")
