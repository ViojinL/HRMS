from decimal import Decimal
from django.db import models
from django.utils.text import slugify
from apps.core.models import BaseModel


class LeaveReasonConfig(BaseModel):
    STATUS_CHOICES = [
        ('enabled', '启用'),
        ('disabled', '禁用'),
    ]

    code = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="编码",
        help_text="全局唯一码，推荐使用拼音/英文"
    )
    name = models.CharField(
        max_length=64,
        verbose_name="名称",
        help_text="例如“年假”“事假”"
    )
    description = models.TextField(
        blank=True,
        verbose_name="描述",
        help_text="用于前端/审批提示的说明"
    )
    max_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="最长天数",
        help_text="自动校验最长可请假天数"
    )
    requires_attachment = models.BooleanField(
        default=False,
        verbose_name="是否需要附件",
        help_text="如病假是否必须上传病假条"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='enabled',
        verbose_name="状态"
    )
    sort_order = models.PositiveSmallIntegerField(
        default=10,
        verbose_name="排序",
        help_text="越小越靠前"
    )

    class Meta(BaseModel.Meta):
        db_table = 'config_leave_reason'
        verbose_name = '请假理由配置'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def _generate_code(self):
        base_code = slugify(self.name or '') or 'reason'
        candidate = base_code
        count = 1
        while LeaveReasonConfig.objects.filter(code=candidate).exclude(pk=self.pk).exists():
            count += 1
            candidate = f"{base_code}-{count}"
        return candidate

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)
