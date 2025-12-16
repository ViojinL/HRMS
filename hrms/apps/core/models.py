from django.db import models
import uuid

class BaseModel(models.Model):
    """
    基础模型，包含所有表公用的字段
    对应《HRMS 开发规则文档》 3.1.1 基础字段规范
    """
    id = models.CharField(
        primary_key=True,
        max_length=50,
        default=uuid.uuid4,
        editable=False,
        help_text="主键ID，采用UUID生成"
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="逻辑删除标识",
        help_text="逻辑删除标识（禁止物理删除）"
    )
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
        help_text="创建时间（禁止手动修改）"
    )
    create_by = models.CharField(
        max_length=64,
        verbose_name="创建人",
        help_text="创建人（关联用户表 ID）"
    )
    update_time = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
        help_text="更新时间（触发器自动更新）"
    )
    update_by = models.CharField(
        max_length=64,
        verbose_name="更新人",
        help_text="更新人（关联用户表 ID）"
    )

    class Meta:
        abstract = True
