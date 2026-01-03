from django.test import TestCase
from decimal import Decimal
from apps.performance.models import PerformanceEvaluation, PerformanceCycle
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

class PerformanceValidationTests(TestCase):
    def setUp(self):
        self.cycle = PerformanceCycle.objects.create(
            cycle_name="校验测试周期",
            cycle_type="monthly",
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(days=30),
            attendance_weight=50,
            leave_weight=50
        )
        
    def test_precision_handling(self):
        """[边界测试] 验证计算逻辑：当出勤率为0.8567时，应计算出正确得分"""
        eval_record = PerformanceEvaluation(
            cycle=self.cycle,
            emp_id=1,
            attendance_rate=Decimal("0.8567"),
            leave_rate=Decimal("0")
        )
        score = eval_record.compute_rule_score()
        # 0.8567 * 50 + (1-0) * 50 = 42.835 + 50 = 92.835
        self.assertAlmostEqual(float(score), 92.835, places=3)

    def test_invalid_negative_input_handling(self):
        """[错误处理测试] 验证系统如何处理负数输入 (业务层面本不应允许负数)"""
        eval_record = PerformanceEvaluation(
            cycle=self.cycle,
            emp_id=1,
            attendance_rate=Decimal("-0.1"), # 输入负数
            leave_rate=Decimal("0.1")
        )
        score = eval_record.compute_rule_score()
        # 即使输入了负数，规则计算仍应按公式执行（或根据业务逻辑决定是否返回None）
        # 这里测试它是否能在异常输入下依然给出一个数值响应而不断开
        self.assertIsInstance(score, Decimal)
        print(f"提示：系统检测到异常输入，当前计算分数为: {score}")

    def test_missing_data_logic(self):
        """[错误处理测试] 验证当核心指标缺失时，系统应返回None而不是报错"""
        eval_record = PerformanceEvaluation(cycle=self.cycle, emp_id=1)
        self.assertIsNone(eval_record.compute_rule_score(), "核心指标缺失时，得分应安全返回为 None")
