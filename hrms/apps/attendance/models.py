from django.db import models
from apps.core.models import BaseModel

class Attendance(BaseModel):
    """
    考勤记录表
    对应《需求文档》 5.2.2 日常考勤管理
    """
    TYPE_CHOICES = [
        ('check_in', '打卡'),
        ('field', '外勤'),
        ('overtime', '加班'),
        ('supplement', '补卡'),
    ]
    
    STATUS_CHOICES = [
        ('normal', '正常'),
        ('late', '迟到'),
        ('early_leave', '早退'),
        ('absent', '旷工'),
        ('leave', '请假'),
        ('field', '外勤'),
        ('overtime', '加班'),
    ]
    
    APPEAL_STATUS_CHOICES = [
        ('none', '无申诉'),
        ('pending', '申诉中'),
        ('approved', '申诉通过'),
        ('rejected', '申诉拒绝'),
    ]
    
    emp = models.ForeignKey(
        'employee.Employee',
        on_delete=models.RESTRICT,
        related_name='attendance_records',
        verbose_name="员工"
    )
    attendance_date = models.DateField(
        verbose_name="考勤日期"
    )
    attendance_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="考勤类型"
    )
    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="上班打卡时间"
    )
    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="下班打卡时间"
    )
    attendance_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="考勤状态"
    )
    exception_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name="异常原因"
    )
    appeal_status = models.CharField(
        max_length=20,
        choices=APPEAL_STATUS_CHOICES,
        default='none',
        verbose_name="申诉状态"
    )

    class Meta:
        db_table = 'attendance'
        verbose_name = '考勤记录'
        verbose_name_plural = verbose_name
        ordering = ['-attendance_date']
        indexes = [
            models.Index(fields=['emp', 'attendance_date']),
            models.Index(fields=['attendance_status', 'attendance_date']),
        ]


class AttendanceShift(BaseModel):
    shift_name = models.CharField(
        max_length=64,
        verbose_name='班次名称',
        default='默认班次'
    )
    check_in_start_time = models.TimeField(
        verbose_name='上班打卡开始时间'
    )
    check_in_end_time = models.TimeField(
        verbose_name='上班打卡结束时间'
    )
    check_out_start_time = models.TimeField(
        verbose_name='下班打卡开始时间'
    )
    check_out_end_time = models.TimeField(
        verbose_name='下班打卡结束时间'
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='启用状态',
        help_text='只有启用状态的班次会被系统作为当前考勤窗口'
    )
    create_by = models.CharField(
        max_length=64,
        default='system',
        verbose_name='创建人'
    )
    update_by = models.CharField(
        max_length=64,
        default='system',
        verbose_name='更新人'
    )

    class Meta:
        db_table = 'attendance_shift'
        verbose_name = '考勤班次'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']

    def __str__(self):
        return self.shift_name

    @classmethod
    def get_active_shift(cls):
        return cls.objects.filter(is_active=True).order_by('-update_time').first()
