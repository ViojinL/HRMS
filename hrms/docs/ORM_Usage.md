# Django ORM 在 HRMS 中的运用

本文档以现有模型与视图为基础，描述 HRMS 如何通过 Django ORM 构建业务逻辑。

## 1. 模型层：字段、关系与元数据
- 所有业务模型都继承自 `apps.core.models.BaseModel`，附带 `create_time` / `update_time` 字段，便于追踪变更。见 [`apps/employee/models.py`](apps/employee/models.py)。
- `Employee` 定义了 `ForeignKey` 向 `organization.Organization`、向自身的 `manager_emp`、以及与 `auth.User` 的 `OneToOneField`，覆盖了员工归属、汇报线与登录用户绑定的三种关系。
- 请假相关模型：`LeaveApply` 将 `emp` 定义为 `ForeignKey('employee.Employee')`，`LeaveTimeSegment` 通过 `leave` 和冗余的 `emp` 关联请假单与员工，在数据库层面为 `EXCLUDE` 约束提供必需字段。两者都保留 `choices` 选项（`leave_type`, `apply_status`）与 `Meta.db_table` 指定表名，便于跨模块引用。

## 2. 视图层：查询、筛选与状态变更
- `LeaveListView.get_queryset()` 直接用 `LeaveApply.objects.filter(emp=...)` 限定当前员工的请假单，再排序交给模板渲染。参考 [`apps/leave/views.py`](apps/leave/views.py#L20-L34)。
- `LeaveApprovalListView` 利用 ORM 的反向关联：先通过 `Employee.objects.filter(manager_emp=current_emp)` 查找下属，再让 `LeaveApply.objects.filter(emp__in=subordinates, apply_status='reviewing')` 获取待审批请求，同时 `.select_related('emp')` 降低访问员工属性的额外查询。详见 [`apps/leave/views.py`](apps/leave/views.py#L76-L111)。
- `LeaveDetailView` 访问 `leave.segments.all()`（反向关联），借助 ORM 自动加载请假段，避免手写 JOIN。审批上下文通过 `leave.emp.manager_emp` 等链式访问完成。参见 [`apps/leave/views.py`](apps/leave/views.py#L134-L200)。
- 状态更改全部使用 ORM 模型更新：`leave.apply_status = 'approved'` + `leave.save()`、`leave.segments.update(is_active=True)` 等，保证信任的业务代码统一记录更新时间。参考 [`apps/leave/views.py`](apps/leave/views.py#L205-L260)。

## 3. 写入与事务控制
- `LeaveApplyView.post()` 在 `transaction.atomic()` 块内：先计算 `total_days`，再使用 `form.save(commit=False)` + 赋值（`leave.emp`, `leave.create_by` 等）保存主表，随后用 `LeaveTimeSegment.objects.create(...)` 生成明细。若 `IntegrityError` 被 `EXCLUDE` 约束拦截，捕获后反馈给用户。见 [`apps/leave/views.py`](apps/leave/views.py#L39-L75)。
- `EmployeeImportView.form_valid()` 遍历 Excel 行：每个员工先 `Employee.objects.filter(emp_id=emp_id).exists()` 做唯一性检查，再 `Employee.objects.create(...)` 与 `User.objects.get_or_create` 结合。整个循环包裹在 `transaction.atomic()` 中，任何异常都会回滚当前行的写入，保持数据一致性。详见 [`apps/employee/views.py`](apps/employee/views.py#L1-L57)。
- `EmployeeCreateView` 通过 `Employee.objects.order_by('-create_time').first()` 决定新工号，之后 `User.objects.create_user()` 生成账户，再保存 `form.instance`。该操作也包裹在 `transaction.atomic()` 里，避免一半写入。参考 [`apps/employee/views.py`](apps/employee/views.py#L57-L103)。

## 4. 查询优化与条件组合
- `EmployeeListView.get_queryset()` 使用 `.select_related('org', 'manager_emp')` 预加载外键，`Q` 对象组合 `emp_name__icontains`、`emp_id__icontains` 与 `org__org_name__icontains`，提供多字段模糊搜索。详见 [`apps/employee/views.py`](apps/employee/views.py#L120-L140)。
- 所有 `ListView` / `DetailView` 都通过 ORM 的 `context` 传递模型实例给模板，模板调用如 `leave.get_leave_type_display()` 等方法是 Django 自动生成的字段选择显示。
- 服务层 `apps.performance.services.refresh_metrics_for_queryset` 直接接受 ORM QuerySet（例如 [`PerformanceEvaluation.objects.filter(...).select_related(...)` in `LeaveApprovalListView`）），保持查询链可复用。

## 5. 原生 SQL 的使用场景
- 当需要跨组织树的多维度聚合结果时，视图 `LeaveOrgSqlSearchView` 和 `EmployeeOrgSqlSearchView` 仍优先查找 ORM 定义的 `vw_leave_profile` / `vw_employee_profile`，再通过 `connection.cursor()` 组合动态 WHERE 子句，保证现有 ORM 不用承担复杂的 CTE 拼接。见 [`apps/leave/views.py`](apps/leave/views.py#L270-L380) 和 [`apps/employee/views.py`](apps/employee/views.py#L140-L220)。
- 原生 SQL 仅在确实需要处理树状授权（如限定部门下属）或查询性能瓶颈时使用，平时业务 CRUD 均通过 ORM 管理表状态和外键完整性。

## 6. 权限与角色控制
- 认证入口：所有核心视图均使用 `LoginRequiredMixin`，未登录即被重定向，保证请求主体可识别；示例见 [apps/leave/views.py](apps/leave/views.py#L12-L124) 与 [apps/employee/views.py](apps/employee/views.py#L11-L120)。
- 细粒度授权：
	- 请假详情/动作：`LeaveDetailView` 校验“本人/直属上级/超管”才可访问，`LeaveActionView` 按审批人或本人完成流转，否则 `PermissionDenied` 或错误提示 [apps/leave/views.py](apps/leave/views.py#L70-L190)。
	- 组织范围查询：`EmployeeOrgSqlSearchView` 通过 `get_user_scope` 解析当前用户的 `is_superuser/is_hr/is_manager` 与可见组织树；非授权角色直接抛出 `PermissionDenied` [apps/employee/views.py](apps/employee/views.py#L120-L210)。
	- 绩效审批：`LeaveApprovalListView` 在查询待办时附加 `is_performance_admin` 判定，只有具备绩效管理员角色的用户才会看到绩效任务 [apps/leave/views.py](apps/leave/views.py#L90-L140)。
- 中间件与上下文：`AuthenticationMiddleware`/`MessageMiddleware` 提供身份与反馈通道，`apps.audit.middleware.AuditMiddleware` 在全局捕获请求上下文供审计，`apps.core.context_processors.user_roles` 将角色标识注入模板，前端可据此控制按钮显隐 [config/settings/base.py](config/settings/base.py#L18-L90)。

## 7. 前后端数据交互流程
- 表单到模型：
	- 请假提交 `POST`：`LeaveApplyView` 校验表单，计算时长后 `form.save(commit=False)` 持久化，再创建时间段，成功后 `messages.success` + redirect，失败时捕获异常并重渲染表单 [apps/leave/views.py](apps/leave/views.py#L36-L90)。
	- 员工导入：`EmployeeImportView` 解析上传 Excel，逐行校验并写库，使用 `messages.success/warning/error` 将结果传给模板，页面通过 Django Messages API 呈现 [apps/employee/views.py](apps/employee/views.py#L15-L90)。
- 列表/详情渲染：`ListView` 与 `DetailView` 默认把 QuerySet/实例注入模板上下文；视图常在 `get_context_data` 中填充衍生字段（如 `leave_type_label`, `segment_rows`）减少模板逻辑 [apps/leave/views.py](apps/leave/views.py#L42-L140)。
- 前端安全：全站启用 `CsrfViewMiddleware`，所有表单在模板中插入 `{% csrf_token %}`；登录/注销跳转在设置中统一指定，未授权请求统一被重定向到登录页 [config/settings/base.py](config/settings/base.py#L41-L90)。
- 与原生 SQL 交互：在少量报表/跨组织查询中，视图先检查所需数据库视图是否存在，再用 `connection.cursor()` 执行参数化 SQL，确保前端输入经过范围约束与参数绑定 [apps/employee/views.py](apps/employee/views.py#L150-L260)。

## 8. 数据唯一性与正确性保障
- 数据库层约束：主键、唯一键与外键在 DDL 中定义，例如 `organization.org_code`、`employee.emp_id/email/id_card` 唯一，所有关联均有外键约束，见 [hrms/hrms_schema.sql](hrms/hrms_schema.sql#L5-L120)。请假时间段冲突由数据库约束（如 `exclude_emp_leave_time`）拦截，视图捕获 `IntegrityError` 给出明确提示 [apps/leave/views.py](apps/leave/views.py#L52-L95)。
- 业务校验（写前）：导入流程先以 ORM `exists()` 校验工号，再检查必填字段与部门编码合法性，非法数据直接累积错误并跳过写库，避免脏数据进入事务 [apps/employee/views.py](apps/employee/views.py#L25-L75)。
- 事务一致性：关键写操作包裹 `transaction.atomic()`，保证主表与子表（如请假申请和时间段）要么同时成功，要么整体回滚；导入循环每行独立事务，单行失败不影响其它行 [apps/leave/views.py](apps/leave/views.py#L49-L90) 与 [apps/employee/views.py](apps/employee/views.py#L46-L85)。
- 选择性预加载与过滤：`select_related`、逻辑删除过滤、`order_by` 保证读取时数据上下文一致且性能可控，减少遗漏关联导致的错误解释或 N+1 性能问题 [apps/leave/views.py](apps/leave/views.py#L15-L60) 与 [apps/employee/views.py](apps/employee/views.py#L100-L160)。

## 9. 总结
HRMS 以 Django ORM 为主干：模型声明字段与关联，视图层使用 QuerySet 完成 CRUD，事务封装保证一致性，`select_related` 提升性能，`ModelForm` 和类视图减少重复代码，必要时通过原生 SQL 补充复杂查询。权限由 LoginRequiredMixin/角色判定/组织范围过滤组合实现，前后端依靠表单与 Messages 统一交互，唯一性与正确性由数据库约束+业务校验+事务共同保障，既保持可维护性也能利用 PostgreSQL 的约束与索引能力。