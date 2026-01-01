## HRMS 数据库结构一览

这份清单覆盖当前代码库里自定义的 PostgreSQL 表、视图、索引与触发器。表结构基于 Django 模型（`hrms/apps/**/models.py`）和手工 SQL（`hrms/db/sql/*`）；如果生产库里加了扩展或分区，请以实际实例为准。

### 一、自定义表（共 12 张）

#### organization
| 字段 | 说明 |
| --- | --- |
| org_code | 组织代码 |
| org_name | 组织名称 |
| org_type | 类型（公司/部门/团队/项目组） |
| parent_org_id | 上级组织（自关联） |
| manager_emp_id | 负责人员工 |
| status | 状态 |
| effective_time | 生效时间 |
| expire_time | 失效时间 |
| create_by | 创建人 |
| update_by | 更新人 |
| update_time | 更新时间（触发器维护） |

#### employee
| 字段 | 说明 |
| --- | --- |
| emp_id | 员工唯一标识 |
| emp_name | 姓名 |
| id_card | 身份证号 |
| gender | 性别 |
| birth_date | 出生日期 |
| phone | 手机 |
| email | 邮箱 |
| hire_date | 入职日期 |
| employment_type | 雇佣类型 |
| emp_status | 员工状态（试用/在职/离职/停薪留职等） |
| org_id | 所属组织 |
| manager_emp_id | 直属上级 |
| user_id | 关联用户 |
| create_by | 创建人 |
| update_by | 更新人 |
| create_time | 创建时间 |
| update_time | 更新时间（触发器维护） |

#### employee_history
| 字段 | 说明 |
| --- | --- |
| emp_id | 员工标识 |
| field_name | 变更字段名 |
| old_value | 旧值 |
| new_value | 新值 |
| change_reason | 变更原因 |
| create_by | 创建人 |
| update_by | 更新人 |
| create_time | 创建时间 |
| update_time | 更新时间 |

#### leave_apply
| 字段 | 说明 |
| --- | --- |
| emp_id | 员工标识 |
| leave_type | 请假类型 |
| apply_status | 申请状态 |
| total_days | 总天数 |
| apply_time | 申请时间 |
| reason | 请假原因 |
| create_by | 创建人 |
| update_by | 更新人 |
| create_time | 创建时间 |
| update_time | 更新时间 |

#### leave_time_segment
| 字段 | 说明 |
| --- | --- |
| leave_id | 对应请假单 |
| emp_id | 员工标识 |
| leave_start_time | 开始时间 |
| leave_end_time | 结束时间 |
| segment_days | 折算天数 |
| is_active | 是否参与时间冲突校验 |
| create_time | 创建时间 |
| update_time | 更新时间 |

#### attendance
| 字段 | 说明 |
| --- | --- |
| emp_id | 员工标识 |
| attendance_date | 出勤日期 |
| attendance_type | 打卡类型 |
| check_in_time | 上班打卡 |
| check_out_time | 下班打卡 |
| attendance_status | 出勤状态 |
| exception_reason | 异常原因 |
| appeal_status | 申诉状态 |
| create_time | 创建时间 |
| update_time | 更新时间 |

#### attendance_shift
| 字段 | 说明 |
| --- | --- |
| shift_name | 班次名称 |
| check_in_start_time | 上班打卡开始 |
| check_in_end_time | 上班打卡结束 |
| check_out_start_time | 下班打卡开始 |
| check_out_end_time | 下班打卡结束 |
| is_active | 是否启用 |
| create_by | 创建人 |
| update_by | 更新人 |
| create_time | 创建时间 |
| update_time | 更新时间 |

#### performance_cycle
| 字段 | 说明 |
| --- | --- |
| cycle_name | 周期名称 |
| cycle_type | 周期类型 |
| start_time | 开始时间 |
| end_time | 结束时间 |
| status | 状态 |
| attendance_weight | 出勤权重 |
| leave_weight | 请假权重 |
| org_id | 适用组织 |
| create_time | 创建时间 |
| update_time | 更新时间 |

#### performance_indicator_set
| 字段 | 说明 |
| --- | --- |
| set_name | 指标集名称 |
| cycle_id | 所属周期 |
| total_weight | 总权重 |
| create_time | 创建时间 |
| update_time | 更新时间 |

#### performance_evaluation
| 字段 | 说明 |
| --- | --- |
| cycle_id | 周期标识 |
| emp_id | 员工标识 |
| indicator_set_id | 指标集 |
| self_score | 自评分 |
| manager_score | 经理评分 |
| final_score | 最终分 |
| attendance_rate | 出勤率 |
| leave_rate | 请假率 |
| rule_score | 规则分 |
| final_remark | 结论备注 |
| evaluation_status | 评估状态 |
| appeal_status | 申诉状态 |
| create_time | 创建时间 |
| update_time | 更新时间 |

#### config_leave_reason
| 字段 | 说明 |
| --- | --- |
| code | 理由编码 |
| name | 理由名称 |
| description | 描述 |
| max_days | 最大天数 |
| requires_attachment | 是否需附件 |
| status | 状态 |
| sort_order | 排序 |
| create_time | 创建时间 |
| update_time | 更新时间 |

#### hrms_audit
| 字段 | 说明 |
| --- | --- |
| oper_user | 操作人 |
| oper_type | 操作类型 |
| summary | 摘要 |
| table_name | 表名 |
| record_id | 记录ID |
| old_data | 旧数据 |
| new_data | 新数据 |
| oper_time | 操作时间 |
| ip_address | IP |
| audit_date | 审计日期 |
| is_deleted | 逻辑删除标识 |
| create_time | 创建时间 |
| update_time | 更新时间 |

### 二、视图（`hrms/db/sql/report_views.sql`）

1. `vw_employee_profile`
	- 汇总：`employee` + 所属 `organization` + 直属上级 `manager_emp`。
	- 字段：`emp_pk`、`emp_id`、`emp_name`、`gender`、`birth_date`、`phone`、`email`、`hire_date`、`position`、`employment_type`、`emp_status`、`org_id/org_code/org_name`、`manager_emp_code`/`manager_emp_name`。
	- 用途：员工列表、SQL 查询、HR 报表。

2. `vw_leave_profile`
	- 汇总：`leave_apply` → 申请人 `employee` → 所属组织，连同 `leave_time_segment` 聚合出的 `start_time`/`end_time`。
	- 字段：`leave_id`、`leave_type`、`apply_status`、`total_days`、`apply_time`、`reason`、员工信息、组织信息、`start_time`、`end_time`。
	- 用途：审批列表与统计。

### 三、索引与约束

- `employee`：索引 `org_id`、`emp_status`、`org_id+emp_status`、`emp_id`、`manager_emp_id`、`hire_date`、`birth_date`。
- `organization`：`parent_org_id`、`manager_emp_id`。
- `leave_apply`：`emp_id`、`apply_status`、`leave_type`、`emp_id+apply_status`。
- `leave_time_segment`：`leave_id`、`emp_id`、`leave_start_time`、`leave_end_time`、`leave_id+start+end`，再加 `exclude_emp_leave_time` 排除约束（`btree_gist`）防止时间重叠。
- `attendance`：模型添加的 `['emp','attendance_date']` 与 `['attendance_status','attendance_date']`。
- 注：若启用 `pg_trgm`，可以额外对 `emp_name`/`position`/`email` 建 gin trigram 索引（脚本注释中保留）。

### 四、触发器

`update_time_trigger.sql` 定义 `update_modified_column()`，将 `NEW.update_time` 设为 `CURRENT_TIMESTAMP`。该函数分别绑定：
- `trigger_organization_update_time`（`organization` 表）
- `trigger_employee_update_time`（`employee` 表）

这保证了 `update_time`/`update_by` 与业务操作保持一致，避免应用层遗漏。

### 五、Django 内建表

| 表名 | 说明 |
| --- | --- |
| `auth_user` | 用户账户，与 `employee.user` 一对一关联。 |
| `auth_group`、`auth_permission`、`auth_user_groups`、`auth_user_user_permissions` | 角色与权限映射。 |
| `django_content_type`、`django_admin_log` | 内容类型定义与后台日志。 |
| `django_session` | 会话存储。 |
| `django_migrations` | 迁移历史。 |
| `django_site` | 站点描述（默认单站）。 |

### 六、附注

- 初始化脚本 `hrms/init_data.py` 会先运行 `migrate/flush`，然后生成组织、员工、绩效、考勤与请假数据，默认密码统一为 `Password123!`；每个生成的员工会写入上述表。
- 业务规则与字段定义详见 `need.md`（枚举值、状态流转、历史追溯、考勤/请假规则等）。在做数据库变更时请同步该文档。
- 如果需要以 PostgreSQL 实例导出完整 schema，可运行 `python manage.py inspectdb` 或查询系统目录；本清单侧重业务层面的表/视图，便于开发与审计核对。