from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.employee.models import Employee
from apps.organization.models import Organization
from apps.performance.models import PerformanceCycle, PerformanceEvaluation


class PerformanceEvaluationModelTests(TestCase):
    def setUp(self) -> None:
        now = timezone.now()
        self.org = Organization.objects.create(
            org_code="PERF-ORG",
            org_name="绩效测试组织",
            org_type="company",
            effective_time=now - timedelta(days=1),
            expire_time=None,
            status="enabled",
            create_by="tests",
            update_by="tests",
        )
        self.cycle = PerformanceCycle.objects.create(
            cycle_name="测试周期",
            cycle_type="monthly",
            start_time=now,
            end_time=now + timedelta(days=30),
            attendance_weight=60,
            leave_weight=40,
            create_by="tests",
            update_by="tests",
        )
        self.employee = Employee.objects.create(
            emp_id="PERF001",
            id_card="420123199001017654",
            emp_name="测试员工",
            gender="male",
            birth_date=date(1990, 1, 1),
            phone="13800000000",
            email="perf@example.com",
            hire_date=date(2020, 1, 1),
            org=self.org,
            position="测试",
            employment_type="full_time",
            emp_status="active",
            create_by="tests",
            update_by="tests",
        )

    def _create_evaluation(
        self,
        attendance_rate: Decimal | None,
        leave_rate: Decimal | None,
        cycle: PerformanceCycle | None = None,
    ) -> PerformanceEvaluation:
        return PerformanceEvaluation.objects.create(
            cycle=cycle or self.cycle,
            emp=self.employee,
            attendance_rate=attendance_rate,
            leave_rate=leave_rate,
            create_by="tests",
            update_by="tests",
        )

    def test_compute_rule_score_normal(self) -> None:
        print("\n[算法验证] 验证常规数值下的绩效加权得分...")
        print(f"[配置] 权重分配: 出勤 {self.cycle.attendance_weight}%, 请假 {self.cycle.leave_weight}%")
        evaluation = self._create_evaluation(
            attendance_rate=Decimal("0.95"), leave_rate=Decimal("0.03")
        )
        score = evaluation.compute_rule_score()
        print(f"[核算结果] 输入: 出勤0.95/请假0.03 -> 计算得分: {score}")
        self.assertIsNotNone(score)
        self.assertEqual(score.quantize(Decimal("0.01")), Decimal("95.80"))
        print("[校验通过] 绩效主路径核算精度符合预期。")

    def test_compute_rule_score_missing_rates(self) -> None:
        print("\n[容错验证] 验证基础数据缺失时的逻辑安全性...")
        evaluation = self._create_evaluation(
            attendance_rate=None, leave_rate=Decimal("0.02")
        )
        print(f"[数据状态] attendance_rate: {evaluation.attendance_rate}, leave_rate: {evaluation.leave_rate}")
        score = evaluation.compute_rule_score()
        self.assertIsNone(score)
        print("[校验通过] 缺失核心数据时方法返回 None，有效防止了计算逻辑崩溃。")

    def test_compute_rule_score_zero_weight(self) -> None:
        print("\n[边界验证] 验证全零权重配置下的系统反应...")
        zero_cycle = PerformanceCycle.objects.create(
            cycle_name="空权重周期",
            cycle_type="monthly",
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(days=30),
            attendance_weight=0,
            leave_weight=0,
            create_by="tests",
            update_by="tests",
        )
        evaluation = self._create_evaluation(
            attendance_rate=Decimal("0.90"),
            leave_rate=Decimal("0.10"),
            cycle=zero_cycle,
        )
        print(f"[周期配置] 出勤占比: {zero_cycle.attendance_weight}, 请假占比: {zero_cycle.leave_weight}")
        self.assertIsNone(evaluation.compute_rule_score())
        print("[校验通过] 面对非法权重配置，系统成功返回空值保护。")

    def test_percentage_properties_rounding(self) -> None:
        print("\n[格式化验证] 验证模型属性的百分比换算与舍入...")
        evaluation = self._create_evaluation(
            attendance_rate=Decimal("0.9234"), leave_rate=Decimal("0.056778")
        )
        print(f"[原始值] 出勤: 0.9234, 请假: 0.056778")
        print(f"[期望展示] 出勤: 92.34%, 请假: 5.68%")
        self.assertEqual(evaluation.attendance_rate_percent, Decimal("92.34"))
        self.assertEqual(evaluation.leave_rate_percent, Decimal("5.68"))
        print("[校验通过] 百分比换算结果符合精度要求。")
