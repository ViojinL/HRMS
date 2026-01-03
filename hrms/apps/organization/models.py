from django.db import models
from apps.core.models import BaseModel


class Organization(BaseModel):
    """
    组织结构表
    对应《需求文档》 5.1.1 组织结构管理
    """

    ORG_TYPE_CHOICES = [
        ("company", "公司"),
        ("department", "部门"),
        ("team", "团队"),
        ("project_group", "项目组"),
    ]

    STATUS_CHOICES = [
        ("enabled", "启用"),
        ("disabled", "禁用"),
    ]

    org_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="组织编码",
        help_text="组织编码，全局唯一",
    )
    org_name = models.CharField(max_length=100, verbose_name="组织名称")
    org_type = models.CharField(
        max_length=20, choices=ORG_TYPE_CHOICES, verbose_name="组织类型"
    )
    parent_org = models.ForeignKey(
        "self",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="上级组织",
        help_text="上级组织ID（顶级节点为空）",
    )
    manager_emp = models.ForeignKey(
        "employee.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_orgs",
        verbose_name="负责人",
        help_text="负责人工号（关联员工表）",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="enabled", verbose_name="状态"
    )
    effective_time = models.DateTimeField(verbose_name="生效时间")
    expire_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="失效时间",
        help_text="失效时间（永久有效为空）",
    )

    class Meta:
        db_table = "organization"
        verbose_name = "组织结构"
        verbose_name_plural = verbose_name
        ordering = ["org_code"]

    def __str__(self):
        return f"{self.org_name} ({self.org_code})"
