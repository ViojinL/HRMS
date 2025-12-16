from django.db import models
from apps.core.models import BaseModel
from django.contrib.auth.models import User

class Employee(BaseModel):
    """
    员工档案表
    对应《需求文档》 5.1.2 员工档案管理
    """
    
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
        ('other', '其他'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', '正式'),
        ('intern', '实习'),
        ('contract', '劳务派遣'),
    ]
    
    EMP_STATUS_CHOICES = [
        ('probation', '试用期'),
        ('active', '在职'),
        ('resigning', '待离职'),
        ('resigned', '离职'),
        ('suspended', '停薪留职'),
    ]

    # 核心字段
    emp_id = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="工号",
        help_text="员工工号（业务唯一标识，区别于系统ID）"
    )
    id_card = models.CharField(
        max_length=18,
        unique=True,
        verbose_name="身份证号",
        help_text="身份证号（加密存储，脱敏显示）"
    )
    emp_name = models.CharField(
        max_length=50,
        verbose_name="姓名"
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        verbose_name="性别"
    )
    birth_date = models.DateField(
        verbose_name="出生日期"
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="手机号"
    )
    email = models.EmailField(
        max_length=100,
        unique=True,
        verbose_name="邮箱"
    )
    hire_date = models.DateField(
        verbose_name="入职日期"
    )
    
    # 关联字段
    org = models.ForeignKey(
        'organization.Organization',
        on_delete=models.RESTRICT,
        related_name='employees',
        verbose_name="所属组织"
    )
    position = models.CharField(
        max_length=50,
        verbose_name="岗位名称"
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name="雇佣类型"
    )
    emp_status = models.CharField(
        max_length=20,
        choices=EMP_STATUS_CHOICES,
        verbose_name="员工状态"
    )
    manager_emp = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name="直接上级",
        help_text="直接上级工号"
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee',
        verbose_name="关联系统用户"
    )

    class Meta:
        db_table = 'employee'
        verbose_name = '员工档案'
        verbose_name_plural = verbose_name
        ordering = ['emp_id']

    def __str__(self):
        return f"{self.emp_name} ({self.emp_id})"

class EmployeeHistory(BaseModel):
    """
    员工历史信息表 (仅用于记录核心信息变更)
    """
    emp = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='history_records',
        verbose_name="关联员工"
    )
    field_name = models.CharField(max_length=50, verbose_name="变更字段")
    old_value = models.TextField(verbose_name="旧值", null=True, blank=True)
    new_value = models.TextField(verbose_name="新值", null=True, blank=True)
    change_reason = models.CharField(max_length=200, verbose_name="变更原因", null=True, blank=True)

    class Meta:
        db_table = 'employee_history'
        verbose_name = '员工变更历史'
        verbose_name_plural = verbose_name
