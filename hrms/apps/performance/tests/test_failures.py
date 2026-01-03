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
            leave_weight=50
        )
        
    def test_normal_calculation(self):
        """测试正常绩效计算：验证出勤率 100% 且无请假时的得分"""
        eval_record = PerformanceEvaluation(
            cycle=self.cycle,
            emp_id=1,
            attendance_rate=Decimal("1.0"),
            leave_rate=Decimal("0.0")
        )
        score = eval_record.compute_rule_score()
        # (1.0 * 100 * 50% + (1-0.0) * 100 * 50%) = 50 + 50 = 100
        self.assertEqual(float(score), 100.0)

    def test_missing_data_returns_none(self):
        """测试异常处理：关键数据缺失时应返回 None 而不应让程序崩溃"""
        eval_record = PerformanceEvaluation(cycle=self.cycle, emp_id=1)
        # 验证 compute_rule_score 遇到 None 值时能正确返回 None
        self.assertIsNone(eval_record.compute_rule_score())
