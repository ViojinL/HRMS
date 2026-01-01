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
        evaluation = self._create_evaluation(
            attendance_rate=Decimal("0.95"), leave_rate=Decimal("0.03")
        )
        score = evaluation.compute_rule_score()
        self.assertIsNotNone(score)
        self.assertEqual(score.quantize(Decimal("0.01")), Decimal("95.80"))

    def test_compute_rule_score_missing_rates(self) -> None:
        evaluation = self._create_evaluation(
            attendance_rate=None, leave_rate=Decimal("0.02")
        )
        self.assertIsNone(evaluation.compute_rule_score())

    def test_compute_rule_score_zero_weight(self) -> None:
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
        self.assertIsNone(evaluation.compute_rule_score())

    def test_percentage_properties_rounding(self) -> None:
        evaluation = self._create_evaluation(
            attendance_rate=Decimal("0.9234"), leave_rate=Decimal("0.056778")
        )
        self.assertEqual(evaluation.attendance_rate_percent, Decimal("92.34"))
        self.assertEqual(evaluation.leave_rate_percent, Decimal("5.68"))
