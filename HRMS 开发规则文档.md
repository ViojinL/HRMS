# HRMS 开发规则文档（完整版）

**技术栈**：Django 5.0 + PostgreSQL 16 + Django Templates + Tailwind CSS 3.x
**设计导向**：数据库主导、强一致性、可审计、易扩展
**文档版本**：v2.0
**生效日期**：2024-12-01
**修订记录**：v1.0（基础框架）→ v2.0（补充落地细节、审计规则、迁移规范）

# 1. 文档目的

本文档规范 HRMS 项目的开发方式、技术边界与落地标准，核心目标：

- 最大化体现数据库设计价值，关键业务规则由 PostgreSQL 强制执行

- 确保应用代码分层清晰、可维护、可审计

- 课程设计验收时，数据库层核心亮点可量化、可验证

- 统一开发规范，降低团队协作成本

# 2. 总体开发原则（强制遵守）

## 2.1 数据库主导原则（最高优先级）

以下核心规则**必须由 PostgreSQL 实现**，禁止仅通过 Django 代码模拟（绕开数据库写入非法数据视为不合格）：

|规则类型|具体场景|数据库实现方式|
|---|---|---|
|唯一性约束|员工工号、身份证号、组织编码|唯一索引（UNIQUE INDEX）|
|外键完整性|员工-组织、请假单-员工、绩效-周期|外键约束（FOREIGN KEY + ON DELETE RESTRICT）|
|时间区间不重叠|请假时间段、绩效周期|排除约束（EXCLUSION CONSTRAINT）+ 触发器|
|状态不可逆|请假状态、绩效状态流转|CHECK 约束 + 触发器|
|历史数据不可篡改|员工核心信息、考勤记录、绩效结果|审计表 + 触发器 + 权限限制|
|组织结构防循环|组织树父节点关联|触发器 + 递归查询校验|
## 2.2 分层职责清晰（禁止跨层越权）

```text

数据库层（PostgreSQL）
├─ 核心能力：约束/触发器/分区/视图/存储过程/执行计划优化
├─ 责任边界：数据正确性兜底、性能优化、审计记录、规则强制执行
└─ 禁止：业务流程编排、页面渲染逻辑

应用层（Django）
├─ 核心能力：事务管理、权限控制、参数校验、流程编排、ORM 封装
├─ 责任边界：接收请求、调用数据库、返回结果、权限判断
└─ 禁止：模拟数据库约束、拼接复杂原生 SQL、模板层写业务逻辑

展示层（Django Templates + Tailwind CSS）
├─ 核心能力：数据展示、表单渲染、样式适配、基础交互
├─ 责任边界：仅负责 UI 呈现，无业务逻辑
└─ 禁止：业务规则判断、权限控制、直接操作数据库
```

## 2.3 明确禁止的做法

- ❌ 在模板中编写业务判断（如 `{% if %}` 做状态流转校验）

- ❌ 在视图函数中拼接复杂原生 SQL（允许通过 `RawSQL`/`Execute` 调用预定义 SQL 文件）

- ❌ 用 ORM 代码“模拟”数据库约束（如在 `save()` 方法中校验唯一性）

- ❌ 前端参数直接决定数据访问范围（如通过 `request.GET` 传递部门 ID 无权限校验）

- ❌ 多表写入时未开启事务（如绩效提交同时写评分表和状态表）

- ❌ 核心数据物理删除（必须逻辑删除）

- ❌ 修改/删除审计表数据（审计表仅允许 INSERT/SELECT）

# 3. 数据库设计规范

## 3.1 表设计通用规则

### 3.1.1 基础字段规范

所有核心业务表必须包含以下通用字段（ORM 抽象为 `BaseModel`）：

|字段名|数据类型（PostgreSQL）|约束|说明|
|---|---|---|---|
|id|VARCHAR(32)|主键|采用 UUID 生成，避免自增 ID 泄露数据量|
|is_deleted|BOOLEAN|NOT NULL DEFAULT false|逻辑删除标识（禁止物理删除）|
|create_time|TIMESTAMP|NOT NULL DEFAULT CURRENT_TIMESTAMP|创建时间（禁止手动修改）|
|create_by|VARCHAR(32)|NOT NULL|创建人（关联用户表 ID）|
|update_time|TIMESTAMP|NOT NULL DEFAULT CURRENT_TIMESTAMP|更新时间（触发器自动更新）|
|update_by|VARCHAR(32)|NOT NULL|更新人（关联用户表 ID）|
### 3.1.2 通用字段自动更新触发器

```sql

-- 通用更新时间触发器函数
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 给员工表绑定触发器示例
CREATE TRIGGER trigger_employee_update_time
BEFORE UPDATE ON employee
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();
```

## 3.2 核心场景数据库实现

### 3.2.1 时间区间不重叠（请假/绩效周期）

**1. 请假时间段不重叠（排除约束）**

```sql

-- 请假时间段表（leave_time_segment）添加排除约束
ALTER TABLE leave_time_segment
ADD CONSTRAINT exclude_emp_leave_time
EXCLUDE USING gist (
    emp_id WITH =,
    tstzrange(leave_start_time, leave_end_time, '[]') WITH &&
);
-- 说明：tstzrange 表示带时区的时间范围，'[]' 表示闭区间，&& 表示重叠
```

**2. 绩效周期不重叠（触发器+索引）**

```sql

-- 绩效周期表复合索引
CREATE UNIQUE INDEX idx_cycle_org_type_time ON performance_cycle (org_id, cycle_type, tstzrange(start_time, end_time, '[]'));

-- 周期重叠校验触发器
CREATE OR REPLACE FUNCTION check_cycle_overlap()
RETURNS TRIGGER AS $$
DECLARE
    overlap_count INT;
BEGIN
    SELECT COUNT(*) INTO overlap_count
    FROM performance_cycle
    WHERE org_id = NEW.org_id
      AND cycle_type = NEW.cycle_type
      AND tstzrange(start_time, end_time, '[]') && tstzrange(NEW.start_time, NEW.end_time, '[]')
      AND is_deleted = false;
    
    IF overlap_count > 0 THEN
        RAISE EXCEPTION '同一组织同类型绩效周期时间重叠，周期ID：%', NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_cycle_overlap
BEFORE INSERT OR UPDATE ON performance_cycle
FOR EACH ROW
EXECUTE FUNCTION check_cycle_overlap();
```

### 3.2.2 高频数据性能设计（考勤表）

**1. 按月分区**

```sql

-- 创建考勤表分区模板
CREATE TABLE attendance (
    id VARCHAR(32) PRIMARY KEY,
    emp_id VARCHAR(32) NOT NULL REFERENCES employee(id) ON DELETE RESTRICT,
    attendance_date DATE NOT NULL,
    attendance_type VARCHAR(20) NOT NULL,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    attendance_status VARCHAR(20) NOT NULL,
    exception_reason TEXT,
    appeal_status VARCHAR(20) NOT NULL DEFAULT '无申诉',
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    create_by VARCHAR(32) NOT NULL,
    update_by VARCHAR(32) NOT NULL
) PARTITION BY RANGE (attendance_date);

-- 批量创建2024年分区脚本
DO $$
DECLARE
    month INT;
    start_date DATE;
    end_date DATE;
BEGIN
    FOR month IN 1..12 LOOP
        start_date := TO_DATE('2024-' || month || '-01', 'YYYY-MM-DD');
        end_date := (start_date + INTERVAL '1 month')::DATE;
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS attendance_2024%02d PARTITION OF attendance FOR VALUES FROM (%L) TO (%L)',
            month, start_date, end_date
        );
    END LOOP;
END $$;
```

**2. 复合索引**

```sql

-- 考勤表核心索引（优化高频查询）
CREATE INDEX idx_attendance_emp_date ON attendance (emp_id, attendance_date) WHERE is_deleted = false;
CREATE INDEX idx_attendance_status_date ON attendance (attendance_status, attendance_date) WHERE is_deleted = false;
```

**3. 性能验收标准**

- 单员工月度考勤查询（带索引）：响应时间 ≤ 100ms（EXPLAIN ANALYZE 验证无全表扫描）

- 部门月度考勤统计（1000+员工）：响应时间 ≤ 500ms

- 考勤表数据量达 100 万条时，新增记录响应时间 ≤ 50ms

### 3.2.3 审计与不可篡改

**1. 审计表设计**

```sql

-- 全局审计表
CREATE TABLE hrms_audit (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL, -- 被操作表名
    record_id VARCHAR(32) NOT NULL,  -- 被操作记录ID
    oper_type VARCHAR(20) NOT NULL CHECK (oper_type IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,                  -- 操作前数据（UPDATE/DELETE）
    new_data JSONB,                  -- 操作后数据（INSERT/UPDATE）
    oper_user VARCHAR(32) NOT NULL,  -- 操作人ID
    oper_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),          -- 操作IP
    audit_date DATE NOT NULL DEFAULT CURRENT_DATE,
    is_deleted BOOLEAN NOT NULL DEFAULT false CHECK (is_deleted = false) -- 禁止删除
);

-- 审计表权限控制
REVOKE UPDATE, DELETE, TRUNCATE ON hrms_audit FROM ALL;
GRANT INSERT, SELECT ON hrms_audit TO hrms_app; -- 应用数据库用户

-- 审计表按月分区
ALTER TABLE hrms_audit PARTITION BY RANGE (audit_date);
CREATE TABLE hrms_audit_202401 PARTITION OF hrms_audit
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

**2. 员工表审计触发器**

```sql

CREATE OR REPLACE FUNCTION audit_employee_operation()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO hrms_audit (table_name, record_id, oper_type, old_data, new_data, oper_user, ip_address, audit_date)
        VALUES ('employee', NEW.id, 'INSERT', NULL, row_to_json(NEW), current_user, inet_client_addr()::varchar, CURRENT_DATE);
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO hrms_audit (table_name, record_id, oper_type, old_data, new_data, oper_user, ip_address, audit_date)
        VALUES ('employee', NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), current_user, inet_client_addr()::varchar, CURRENT_DATE);
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO hrms_audit (table_name, record_id, oper_type, old_data, new_data, oper_user, ip_address, audit_date)
        VALUES ('employee', OLD.id, 'DELETE', row_to_json(OLD), NULL, current_user, inet_client_addr()::varchar, CURRENT_DATE);
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 绑定触发器
CREATE TRIGGER trigger_audit_employee
AFTER INSERT OR UPDATE OR DELETE ON employee
FOR EACH ROW
EXECUTE FUNCTION audit_employee_operation();
```

## 3.3 数据库迁移规范

### 3.3.1 迁移分层管理

```text

db/
├─ migrations/          # Django ORM 迁移文件（基础模型）
│ ├─ 0001_initial.py    # 员工、组织等基础表结构
│ └─ 0002_add_status.py # 状态字段新增
├─ sql/                 # 原生 SQL 迁移文件（核心约束/触发器/分区）
│ ├─ attendance_partition.sql  # 考勤表分区
│ ├─ leave_overlap_guard.sql   # 请假时间重叠约束
│ └─ audit_triggers.sql        # 审计触发器
└─ README.md            # 迁移执行说明
```

### 3.3.2 原生 SQL 迁移集成

```python

# apps/attendance/migrations/0003_attendance_partition.py
from django.db import migrations
import os

def apply_partition_sql(apps, schema_editor):
    sql_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'db/sql/attendance_partition.sql'
    )
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    schema_editor.execute(sql)

class Migration(migrations.Migration):
    dependencies = [('attendance', '0002_auto_20240101_0000')]
    operations = [
        migrations.RunSQL(sql=apply_partition_sql, reverse_sql=migrations.RunSQL.noop)
    ]
```

# 4. ORM 与原生 SQL 使用规则

## 4.1 必须使用 ORM 的场景

- 基础模型 CRUD（员工、组织、配置表）

- 列表查询、分页、排序（如员工列表、考勤记录列表）

- 状态字段更新（前提：数据库约束兜底）

- RBAC 关系表操作（用户-角色-权限）

**规则**：ORM 仅作为数据库操作的“便捷入口”，不得依赖 ORM 实现业务规则校验。

## 4.2 必须使用原生 SQL 的场景

- 考勤表分区管理

- 请假时间重叠约束

- 组织结构防循环触发器

- 绩效结果视图查询

- 复杂统计查询（如跨表多维度绩效分析）

**规则**：原生 SQL 必须放在 `db/sql/` 目录，通过参数化传参防注入：

```python

# 正确示例：参数化查询
from django.db import connection

def get_employee_audit(emp_id):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM hrms_audit WHERE table_name = 'employee' AND record_id = %s",
            [emp_id]  # 参数化传参，防 SQL 注入
        )
        return cursor.fetchall()
```

# 5. Django 项目结构规范

```text

hrms/
├─ config/                # 项目配置
│ ├─ settings/
│ │ ├─ base.py            # 基础配置
│ │ └─ prod.py            # 生产环境配置
│ ├─ urls.py              # 全局路由
│ └─ wsgi.py              # WSGI 配置
├─ apps/                  # 业务模块
│ ├─ organization/        # 组织管理
│ │ ├─ models.py          # 组织模型（ORM）
│ │ ├─ views.py           # 组织视图
│ │ ├─ forms.py           # 组织表单
│ │ ├─ urls.py            # 组织路由
│ │ └─ migrations/        # 组织迁移文件
│ ├─ employee/            # 员工管理（同上）
│ ├─ attendance/          # 考勤管理（同上）
│ ├─ leave/               # 请假管理（同上）
│ ├─ performance/         # 绩效管理（同上）
│ ├─ rbac/                # 权限管理
│ └─ audit/               # 审计查询
├─ templates/             # 模板文件
│ ├─ base.html            # 基础模板
│ ├─ organization/        # 组织模板
│ ├─ employee/            # 员工模板
│ └─ components/          # 公共组件（按钮、表单）
├─ static/                # 静态资源
│ ├─ css/                 # Tailwind 编译后样式
│ ├─ js/                  # 基础交互 JS
│ └─ images/              # 图片资源
├─ db/                    # 数据库相关
│ ├─ migrations/          # ORM 迁移
│ ├─ sql/                 # 原生 SQL
│ └─ README.md            # 迁移说明
├─ utils/                 # 工具函数
│ ├─ auth.py              # 权限工具
│ ├─ db.py                # 数据库工具
│ └─ validators.py        # 参数校验工具
└─ manage.py              # Django 管理入口
```

# 6. Django 编码规则

## 6.1 View 层规则

**职责边界**：仅做参数校验、权限判断、调用 Service、返回响应，禁止复杂 SQL 拼接。

**代码示例（请假提交）**：

```python

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from apps.leave.forms import LeaveApplyForm
from apps.leave.models import LeaveApply, LeaveTimeSegment
from utils.auth import check_permission

@check_permission('leave:apply')  # 权限装饰器
def leave_apply(request):
    if request.method == 'POST':
        form = LeaveApplyForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():  # 事务保证原子性
                    # 1. 保存请假主表
                    leave_apply = form.save(commit=False)
                    leave_apply.create_by = request.user.id
                    leave_apply.update_by = request.user.id
                    leave_apply.save()
                    
                    # 2. 保存请假时间段
                    segments = form.cleaned_data.get('segments')
                    for segment in segments:
                        LeaveTimeSegment.objects.create(
                            leave_id=leave_apply.id,
                            leave_start_time=segment['start_time'],
                            leave_end_time=segment['end_time'],
                            segment_days=segment['days'],
                            create_by=request.user.id,
                            update_by=request.user.id
                        )
                messages.success(request, '请假申请提交成功')
                return redirect('leave:list')
            except Exception as e:
                messages.error(request, f'提交失败：{str(e)}')
    else:
        form = LeaveApplyForm()
    return render(request, 'leave/apply.html', {'form': form})
```

## 6.2 Model 层规则

- 基础模型继承 `BaseModel`（包含通用字段）

- 状态字段使用 `choices` 枚举，与数据库约束一致

- 禁止在 `save()` 方法中实现业务规则校验

```python

# apps/leave/models.py
import uuid
from django.db import models

class LeaveApply(models.Model):
    LEAVE_STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approving', '审批中'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('cancelled', '已撤销'),
        ('invalid', '已作废'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emp_id = models.ForeignKey('employee.Employee', on_delete=models.RESTRICT)
    leave_type = models.CharField(max_length=20)
    apply_status = models.CharField(max_length=20, choices=LEAVE_STATUS_CHOICES)
    # 通用字段
    is_deleted = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    create_by = models.CharField(max_length=32)
    update_by = models.CharField(max_length=32)
    
    class Meta:
        db_table = 'leave_apply'
        verbose_name = '请假申请'
```

## 6.3 Template 层规则

- 仅负责展示数据、渲染表单，禁止业务判断

- 使用 Tailwind CSS 实现样式，禁止内联样式

- 表单仅做基础格式校验，业务规则由后端负责

```html

{% extends 'base.html' %}
{% block content %}
 
      {{ form.leave_type }}
      {% if form.leave_type.errors %}
        {{ form.leave_type.errors.0 }}
      {% endif %}
   
{% endblock %}
```

# 7. 权限与数据范围控制规则

## 7.1 RBAC 权限模型

|角色|功能权限|数据权限|
|---|---|---|
|普通员工|本人信息查看、请假申请、考勤查看|仅本人数据|
|部门负责人|部门员工查看、请假审批、绩效评估|本部门及子部门数据|
|HR|所有员工管理、考勤统计、绩效配置|全公司数据|
|系统管理员|系统配置、权限管理、审计查询|全公司数据|
## 7.2 权限实现规则

```python

# utils/auth.py
def check_data_scope(user, emp_id):
    """校验用户是否有权限访问指定员工数据"""
    if user.is_superuser or user.has_role('HR'):
        return True
    if user.has_role('部门负责人'):
        # 查询员工所属部门是否在用户管辖范围内
        emp_dept = Employee.objects.get(id=emp_id).org_id
        return user.dept_id in get_all_sub_depts(emp_dept)
    # 普通员工仅能访问本人数据
    return emp_id == user.emp_id
```

# 8. 前端规范

## 8.1 UI 风格

- 白色简约风格，符合企业后台审美

- 统一配色：主色（蓝色 #165DFF）、成功色（绿色 #00B42A）、错误色（红色 #F53F3F）

- 信息层级清晰（标题 > 内容 > 辅助信息）

## 8.2 样式规范

- 使用 Tailwind CSS 原子类，禁止自定义 CSS（公共样式除外）

- 响应式适配：支持 1366×768、1920×1080 分辨率

- 公共组件集中维护（如 `templates/components/button.html`）

# 9. 验收标准

## 9.1 功能验收

- 核心业务场景功能完整（组织、员工、考勤、请假、绩效）

- 数据库约束生效（时间重叠、组织循环等非法操作被拦截）

- 权限控制精准，无越权访问

## 9.2 性能验收

- 高频查询响应时间符合要求

- 并发 50 用户操作无数据不一致

- 数据库无慢查询（执行时间 > 1s）

## 9.3 可审计验收

- 核心表操作均记录到审计表

- 审计记录不可修改/删除

- 支持按条件查询审计记录

# 10. 附录

## 10.1 术语定义

|术语|定义|
|---|---|
|逻辑删除|通过字段标识数据删除状态，物理数据仍保留|
|排除约束|PostgreSQL 特有的约束，用于防止时间/范围重叠|
|分区表|将大表按时间/范围拆分为多个子表，提升查询性能|
## 10.2 开发环境要求

- Python 3.11+

- Django 5.0+

- PostgreSQL 16+

- Tailwind CSS 3.x

- 代码规范：PEP 8（使用 black 格式化）
> （注：文档部分内容可能由 AI 生成）