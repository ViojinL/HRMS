from django.db import models
from apps.core.models import BaseModel
from decimal import Decimal


class PerformanceCycle(BaseModel):
    """
    绩效周期表
    对应《需求文档》 5.3.1 绩效周期与规则配置
    """

    CYCLE_TYPE_CHOICES = [
        ("monthly", "月度"),
        ("quarterly", "季度"),
        ("semiannual", "半年度"),
        ("annual", "年度"),
    ]

    STATUS_CHOICES = [
        ("not_started", "未开始"),
        ("in_progress", "进行中"),
        ("ended", "已结束"),
        ("archived", "已归档"),
    ]

    cycle_name = models.CharField(max_length=100, verbose_name="周期名称")
    cycle_type = models.CharField(
        max_length=20, choices=CYCLE_TYPE_CHOICES, verbose_name="周期类型"
    )
    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_started",
        verbose_name="状态",
    )

    attendance_weight = models.PositiveSmallIntegerField(
        default=50, verbose_name="出勤率占比(%)", help_text="用于规则计算，0-100"
    )
    leave_weight = models.PositiveSmallIntegerField(
        default=50, verbose_name="请假率占比(%)", help_text="用于规则计算，0-100"
    )
    org = models.ForeignKey(
        "organization.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="适用组织",
        help_text="空表示全公司",
    )

    class Meta:
        db_table = "performance_cycle"
        verbose_name = "绩效周期"
        verbose_name_plural = verbose_name
        ordering = ["-start_time"]

    def __str__(self):
        return self.cycle_name


class PerformanceEvaluation(BaseModel):
    """
    绩效评估记录
    """

    EVAL_STATUS_CHOICES = [
        ("not_started", "未开始"),
        ("hr_audit", "绩效部门审核中"),
        ("completed", "已完成"),
    ]

    APPEAL_STATUS_CHOICES = [
        ("none", "无申诉"),
        ("pending", "申诉中"),
        ("approved", "申诉通过"),
        ("rejected", "申诉拒绝"),
    ]

    cycle = models.ForeignKey(
        PerformanceCycle, on_delete=models.CASCADE, verbose_name="绩效周期"
    )
    emp = models.ForeignKey(
        "employee.Employee", on_delete=models.CASCADE, verbose_name="被评估人"
    )
    final_score = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="最终总分"
    )

    attendance_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="出勤率",
        help_text="0-1 之间",
    )
    leave_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="请假率",
        help_text="0-1 之间",
    )
    rule_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="规则得分",
        help_text="依据出勤/请假规则计算，0-100",
    )
    final_remark = models.TextField(null=True, blank=True, verbose_name="最终评价")
    evaluation_status = models.CharField(
        max_length=20,
        choices=EVAL_STATUS_CHOICES,
        default="not_started",
        verbose_name="评估状态",
    )
    appeal_status = models.CharField(
        max_length=20,
        choices=APPEAL_STATUS_CHOICES,
        default="none",
        verbose_name="申诉状态",
    )

    class Meta:
        db_table = "performance_evaluation"
        verbose_name = "绩效评估"
        verbose_name_plural = verbose_name

    def compute_rule_score(self) -> Decimal | None:
        """按周期规则计算规则得分(0-100)。

        规则：
        - 出勤分 = 出勤率 * 100
        - 请假分 = (1 - 请假率) * 100
        - 总分 = 出勤分 * 出勤权重 + 请假分 * 请假权重
        """
        if self.attendance_rate is None or self.leave_rate is None:
            return None
        cycle = self.cycle
        total_weight = Decimal(cycle.attendance_weight + cycle.leave_weight)
        if total_weight <= 0:
            return None

        attendance_score = Decimal(self.attendance_rate) * Decimal("100")
        leave_score = (Decimal("1") - Decimal(self.leave_rate)) * Decimal("100")
        weighted = (
            attendance_score * Decimal(cycle.attendance_weight)
            + leave_score * Decimal(cycle.leave_weight)
        ) / total_weight
        return weighted

    @property
    def attendance_rate_percent(self) -> Decimal | None:
        if self.attendance_rate is None:
            return None
        return (Decimal(self.attendance_rate) * Decimal("100")).quantize(
            Decimal("0.01")
        )

    @property
    def leave_rate_percent(self) -> Decimal | None:
        if self.leave_rate is None:
            return None
        return (Decimal(self.leave_rate) * Decimal("100")).quantize(Decimal("0.01"))
