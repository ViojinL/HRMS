from django.db import models

class AuditLog(models.Model):
    """
    审计日志表
    对应《需求文档》 7.1 与 规则文档 3.2.3
    注意：此表通常较大，建议按月分区，这里定义Django模型进行查询
    """
    OPER_TYPE_CHOICES = [
        ('INSERT', '新增'),
        ('UPDATE', '修改'),
        ('DELETE', '删除'),
        ('LOGIN', '登录'),
        ('LOGOUT', '登出'),
        ('ACCESS', '访问'),
        ('APPROVE', '审批'),
    ]

    id = models.BigAutoField(primary_key=True)
    table_name = models.CharField(max_length=50, verbose_name="模块/表名", null=True, blank=True)
    record_id = models.CharField(max_length=50, verbose_name="记录ID/URL", null=True, blank=True)
    oper_type = models.CharField(max_length=20, choices=OPER_TYPE_CHOICES, verbose_name="操作类型")
    summary = models.CharField(max_length=200, null=True, blank=True, verbose_name="操作摘要")
    old_data = models.JSONField(null=True, blank=True, verbose_name="操作前数据")
    new_data = models.JSONField(null=True, blank=True, verbose_name="操作后数据")
    oper_user = models.CharField(max_length=32, verbose_name="操作人")
    oper_time = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")
    audit_date = models.DateField(auto_now_add=True, verbose_name="审计日期")
    is_deleted = models.BooleanField(default=False, verbose_name="逻辑删除")

    class Meta:
        db_table = 'hrms_audit'
        verbose_name = '审计日志'
        verbose_name_plural = verbose_name
        ordering = ['-oper_time']

    def __str__(self):
        return f"{self.table_name} - {self.oper_type} - {self.oper_time}"
