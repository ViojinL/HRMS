from django.db import models
from apps.core.models import BaseModel
import uuid

class LeaveApply(BaseModel):
    """
    请假申请主表
    对应《需求文档》 5.2.1 请假管理
    """
    LEAVE_TYPE_CHOICES = [
        ('personal', '事假'),
        ('sick', '病假'),
        ('annual', '年假'),
        ('marriage', '婚假'),
        ('maternity', '产假'),
        ('paternity', '陪产假'),
        ('funeral', '丧假'),
        ('injury', '工伤假'),
        ('lieu', '调休假'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approving', '审批中'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('cancelled', '已撤销'),
        ('invalid', '已作废'),
    ]
    
    emp = models.ForeignKey(
        'employee.Employee',
        on_delete=models.RESTRICT,
        related_name='leave_applications',
        verbose_name="申请人",
        help_text="申请人工号"
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPE_CHOICES,
        verbose_name="请假类型"
    )
    apply_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="申请状态"
    )
    apply_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="提交时间"
    )
    reason = models.TextField(
        null=True,
        blank=True,
        verbose_name="请假事由"
    )
    attachment_url = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="附件路径"
    )
    total_days = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="总天数"
    )

    class Meta:
        db_table = 'leave_apply'
        verbose_name = '请假申请'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.emp.emp_name} - {self.get_leave_type_display()}"


class LeaveTimeSegment(BaseModel):
    """
    请假时间段明细表（支持分段请假）
    """
    leave = models.ForeignKey(
        LeaveApply,
        on_delete=models.CASCADE,
        related_name='segments',
        verbose_name="关联请假单"
    )
    emp = models.ForeignKey(
        'employee.Employee',
        on_delete=models.CASCADE,
        related_name='leave_segments',
        verbose_name="员工",
        help_text="冗余字段，用于数据库时间重叠约束"
    )
    leave_start_time = models.DateTimeField(
        verbose_name="开始时间"
    )
    leave_end_time = models.DateTimeField(
        verbose_name="结束时间"
    )
    segment_days = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="该段天数"
    )

    class Meta:
        db_table = 'leave_time_segment'
        verbose_name = '请假时间段'
        verbose_name_plural = verbose_name
