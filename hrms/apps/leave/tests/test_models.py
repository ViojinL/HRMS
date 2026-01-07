from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.employee.models import Employee
from apps.leave.models import LeaveApply, LeaveTimeSegment
from apps.organization.models import Organization


class LeaveModelTests(TestCase):
    def setUp(self) -> None:
        self.org = Organization.objects.create(
            org_code="ORG-LEAVE",
            org_name="请假组织",
            org_type="company",
            effective_time=timezone.now(),
            status="enabled",
            create_by="tests",
            update_by="tests",
        )
        self.emp = Employee.objects.create(
            emp_id="L001",
            id_card="420123199001010001",
            emp_name="请假员工",
            gender="male",
            birth_date=timezone.now().date(),
            phone="13800000002",
            email="leave@example.com",
            hire_date=timezone.now().date(),
            org=self.org,
            position="工程师",
            employment_type="full_time",
            emp_status="active",
            create_by="tests",
            update_by="tests",
        )

    def test_leave_apply_str_and_defaults(self) -> None:
        print("\n[业务验证] 验证请假申请的默认状态与标识格式...")
        leave = LeaveApply.objects.create(
            emp=self.emp,
            leave_type="annual",
            reason="年度休假",
            total_days=2,
            create_by="tests",
            update_by="tests",
        )
        print(f"[申请创建] 员工: {self.emp.emp_name}, 类型: {leave.get_leave_type_display()}")
        self.assertEqual(str(leave), "请假员工 - 年假")
        self.assertEqual(leave.apply_status, "reviewing")
        print(f"[校验通过] 默认审批状态: {leave.get_apply_status_display()}")

    def test_leave_segments_attach_and_sum(self) -> None:
        print("\n[模型验证] 验证请假申请与时间段的关联性...")
        leave = LeaveApply.objects.create(
            emp=self.emp,
            leave_type="sick",
            total_days=1,
            create_by="tests",
            update_by="tests",
        )
        start = timezone.now()
        segment = LeaveTimeSegment.objects.create(
            leave=leave,
            emp=self.emp,
            leave_start_time=start,
            leave_end_time=start + timedelta(hours=8),
            segment_days=1,
            create_by="tests",
            update_by="tests",
        )
        print(f"[明细录入] 为申请 ID {leave.id} 添加了 8 小时的时间段明细")
        self.assertEqual(leave.segments.count(), 1)
        self.assertEqual(str(leave.segments.first().id), str(segment.id))
        print("[校验通过] 时间段正确挂载至请假主表。")
