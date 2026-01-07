from django.test import TestCase
from decimal import Decimal
from apps.performance.models import PerformanceEvaluation, PerformanceCycle
from django.utils import timezone
from datetime import timedelta


class PerformanceValidationTests(TestCase):
    def setUp(self):
        self.cycle = PerformanceCycle.objects.create(
            cycle_name="性能边界校验",
            cycle_type="monthly",
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(days=30),
            attendance_weight=50,
            leave_weight=50,
        )

    def test_normal_calculation(self):
        """测试正常绩效计算：验证出勤率 100% 且无请假时的得分"""
        print("\n[业务逻辑] 验证满额出勤且无请假场景下的绩效得分...")
        eval_record = PerformanceEvaluation(
            cycle=self.cycle,
            emp_id=1,
            attendance_rate=Decimal("1.0"),
            leave_rate=Decimal("0.0"),
        )
        score = eval_record.compute_rule_score()
        print(f"[计算结果] 出勤率: 1.0, 请假率: 0.0 -> 计算得分: {score}")
        # (1.0 * 100 * 50% + (1-0.0) * 100 * 50%) = 50 + 50 = 100
        self.assertEqual(float(score), 100.0)
        print("[校验通过] 满分计算逻辑正确。")

    def test_missing_data_returns_none(self):
        """测试异常处理：关键数据缺失时应返回 None 而不应让程序崩溃"""
        print("\n[异常校验] 验证缺失出勤/请假数据时的容错处理...")
        eval_record = PerformanceEvaluation(cycle=self.cycle, emp_id=1)
        # 验证 compute_rule_score 遇到 None 值时能正确返回 None
        print(f"[数据状态] attendance_rate: {eval_record.attendance_rate}, leave_rate: {eval_record.leave_rate}")
        self.assertIsNone(eval_record.compute_rule_score())
        print("[校验通过] 系统在缺失数据时能够安全返回 None，未发生崩溃。")
