from django.db import models
from apps.core.models import BaseModel

class PerformanceCycle(BaseModel):
    """
    绩效周期表
    对应《需求文档》 5.3.1 绩效周期与规则配置
    """
    CYCLE_TYPE_CHOICES = [
        ('monthly', '月度'),
        ('quarterly', '季度'),
        ('semiannual', '半年度'),
        ('annual', '年度'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', '未开始'),
        ('in_progress', '进行中'),
        ('ended', '已结束'),
        ('archived', '已归档'),
    ]
    
    cycle_name = models.CharField(
        max_length=100,
        verbose_name="周期名称"
    )
    cycle_type = models.CharField(
        max_length=20,
        choices=CYCLE_TYPE_CHOICES,
        verbose_name="周期类型"
    )
    start_time = models.DateTimeField(
        verbose_name="开始时间"
    )
    end_time = models.DateTimeField(
        verbose_name="结束时间"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started',
        verbose_name="状态"
    )
    org = models.ForeignKey(
        'organization.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="适用组织",
        help_text="空表示全公司"
    )

    class Meta:
        db_table = 'performance_cycle'
        verbose_name = '绩效周期'
        verbose_name_plural = verbose_name
        ordering = ['-start_time']

    def __str__(self):
        return self.cycle_name


class PerformanceIndicatorSet(BaseModel):
    """
    绩效指标集
    """
    set_name = models.CharField(
        max_length=100,
        verbose_name="指标集名称"
    )
    cycle = models.ForeignKey(
        PerformanceCycle,
        on_delete=models.CASCADE,
        related_name='indicator_sets',
        verbose_name="关联周期"
    )
    total_weight = models.PositiveSmallIntegerField(
        default=100,
        verbose_name="总权重",
        help_text="固定100"
    )

    class Meta:
        db_table = 'performance_indicator_set'
        verbose_name = '绩效指标集'
        verbose_name_plural = verbose_name


class PerformanceEvaluation(BaseModel):
    """
    绩效评估记录
    """
    EVAL_STATUS_CHOICES = [
        ('not_started', '未开始'),
        ('self_eval', '自评中'),
        ('manager_eval', '上级评估中'),
        ('hr_audit', 'HR审核中'),
        ('completed', '已完成'),
    ]
    
    APPEAL_STATUS_CHOICES = [
        ('none', '无申诉'),
        ('pending', '申诉中'),
        ('approved', '申诉通过'),
        ('rejected', '申诉拒绝'),
    ]

    cycle = models.ForeignKey(
        PerformanceCycle,
        on_delete=models.CASCADE,
        verbose_name="绩效周期"
    )
    emp = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        verbose_name="被评估人"
    )
    indicator_set = models.ForeignKey(
        PerformanceIndicatorSet,
        on_delete=models.RESTRICT,
        verbose_name="指标集"
    )
    self_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="自评总分"
    )
    manager_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="上级评估总分"
    )
    final_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="最终总分"
    )
    final_remark = models.TextField(
        null=True,
        blank=True,
        verbose_name="最终评价"
    )
    evaluation_status = models.CharField(
        max_length=20,
        choices=EVAL_STATUS_CHOICES,
        default='not_started',
        verbose_name="评估状态"
    )
    appeal_status = models.CharField(
        max_length=20,
        choices=APPEAL_STATUS_CHOICES,
        default='none',
        verbose_name="申诉状态"
    )

    class Meta:
        db_table = 'performance_evaluation'
        verbose_name = '绩效评估'
        verbose_name_plural = verbose_name
