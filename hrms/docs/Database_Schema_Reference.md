# 数据库表结构与关系说明文档

本文档详细列出了 HRMS 系统中的所有数据库表结构、字段定义以及表之间的关联关系。

## 1. 数据库表概览

系统包含以下 11 张核心业务表：

1.  **organization**: 组织架构表
2.  **employee**: 员工档案表
3.  **employee_history**: 员工履历/变更记录表
4.  **attendance**: 考勤记录表
5.  **attendance_shift**: 考勤班次配置表
6.  **leave_apply**: 请假申请表
7.  **leave_time_segment**: 请假时间段明细表
8.  **config_leave_reason**: 请假类型配置表
9.  **performance_cycle**: 绩效周期表
10. **performance_evaluation**: 绩效评估结果表
11. **hrms_audit**: 审计日志表

---

## 2. 详细表结构

### 2.1 组织与员工模块

#### 1. organization (组织架构表)
存储公司的组织结构树。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| org_code | varchar(50) | UNIQUE, NOT NULL | 组织代码 (如: DEPT001) |
| org_name | varchar(100) | NOT NULL | 组织名称 |
| org_type | varchar(20) | NOT NULL | 组织类型 (公司/部门/小组) |
| status | varchar(20) | NOT NULL | 状态 (Active/Inactive) |
| effective_time | timestamptz | NOT NULL | 生效时间 |
| expire_time | timestamptz | | 失效时间 |
| manager_emp_id | varchar(50) | FK | 部门负责人ID (关联 employee) |
| parent_org_id | varchar(50) | FK | 上级组织ID (关联 organization) |
| is_deleted | boolean | NOT NULL | 逻辑删除标记 |
| create_time | timestamptz | | 创建时间 |
| update_time | timestamptz | | 更新时间 |

#### 2. employee (员工表)
存储员工基本信息及归属关系。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| emp_id | varchar(32) | UNIQUE, NOT NULL | 工号 |
| emp_name | varchar(50) | NOT NULL | 姓名 |
| id_card | varchar(18) | UNIQUE, NOT NULL | 身份证号 |
| gender | varchar(10) | NOT NULL | 性别 |
| birth_date | date | NOT NULL | 出生日期 |
| phone | varchar(20) | NOT NULL | 手机号 |
| email | varchar(100) | UNIQUE, NOT NULL | 邮箱 |
| hire_date | date | NOT NULL | 入职日期 |
| position | varchar(50) | NOT NULL | 职位 |
| employment_type | varchar(20) | NOT NULL | 雇佣类型 (全职/实习) |
| emp_status | varchar(20) | NOT NULL | 员工状态 (在职/离职) |
| manager_emp_id | varchar(50) | FK | 直属上级ID (关联 employee) |
| org_id | varchar(50) | FK, NOT NULL | 所属组织ID (关联 organization) |
| user_id | integer | UNIQUE | 关联 Django User ID |
| is_deleted | boolean | NOT NULL | 逻辑删除标记 |
| create_time | timestamptz | | 创建时间 |
| update_time | timestamptz | | 更新时间 |

#### 3. employee_history (员工履历表)
记录员工关键信息的变更历史。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| emp_id | varchar(50) | FK, NOT NULL | 关联员工ID |
| field_name | varchar(50) | NOT NULL | 变更字段名 |
| old_value | text | | 旧值 |
| new_value | text | | 新值 |
| change_reason | varchar(200) | | 变更原因 |
| create_time | timestamptz | | 变更时间 |

### 2.2 考勤与请假模块

#### 4. attendance (考勤记录表)
存储每日打卡及考勤状态。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| emp_id | varchar(50) | FK, NOT NULL | 关联员工ID |
| attendance_date | date | NOT NULL | 考勤日期 |
| attendance_type | varchar(20) | NOT NULL | 打卡类型 (正常/外勤) |
| check_in_time | timestamptz | | 上班打卡时间 |
| check_out_time | timestamptz | | 下班打卡时间 |
| attendance_status | varchar(20) | NOT NULL | 考勤状态 (正常/迟到/早退/缺卡) |
| exception_reason | text | | 异常原因 |
| appeal_status | varchar(20) | NOT NULL | 申诉状态 |
| is_deleted | boolean | NOT NULL | 逻辑删除标记 |

#### 5. attendance_shift (考勤班次配置表)
定义上下班时间规则。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| shift_name | varchar(64) | NOT NULL | 班次名称 |
| check_in_start_time | time | NOT NULL | 上班打卡开始时间 |
| check_in_end_time | time | NOT NULL | 上班打卡结束时间 |
| check_out_start_time | time | NOT NULL | 下班打卡开始时间 |
| check_out_end_time | time | NOT NULL | 下班打卡结束时间 |
| is_active | boolean | NOT NULL | 是否启用 |

#### 6. leave_apply (请假申请表)
请假单据主表。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| emp_id | varchar(50) | FK, NOT NULL | 申请人ID |
| leave_type | varchar(20) | NOT NULL | 请假类型 (年假/病假等) |
| apply_status | varchar(20) | NOT NULL | 申请状态 (待审批/通过/拒绝) |
| apply_time | timestamptz | NOT NULL | 申请时间 |
| reason | text | | 请假事由 |
| attachment_url | varchar(255) | | 附件URL |
| total_days | numeric(10,2) | NOT NULL | 请假总天数 |
| is_deleted | boolean | NOT NULL | 逻辑删除标记 |

#### 7. leave_time_segment (请假时间段明细表)
请假单的具体时间段拆分，用于精确计算和冲突检测。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| leave_id | varchar(50) | FK, NOT NULL | 关联申请ID |
| emp_id | varchar(50) | FK, NOT NULL | 关联员工ID (冗余字段，用于排除约束) |
| leave_start_time | timestamptz | NOT NULL | 开始时间 |
| leave_end_time | timestamptz | NOT NULL | 结束时间 |
| segment_days | numeric(10,2) | NOT NULL | 该段天数 |
| is_active | boolean | NOT NULL | 是否有效 |

#### 8. config_leave_reason (请假类型配置表)
系统字典表，定义请假类型规则。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| code | varchar(32) | UNIQUE, NOT NULL | 类型代码 |
| name | varchar(64) | NOT NULL | 类型名称 |
| description | text | NOT NULL | 描述 |
| max_days | numeric(5,2) | NOT NULL | 单次最大天数限制 |
| requires_attachment | boolean | NOT NULL | 是否必须上传附件 |
| status | varchar(20) | NOT NULL | 状态 |

### 2.3 绩效模块

#### 9. performance_cycle (绩效周期表)
定义考核的时间窗口和规则。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| cycle_name | varchar(100) | NOT NULL | 周期名称 (如: 2024 Q1) |
| cycle_type | varchar(20) | NOT NULL | 周期类型 (月度/季度/年度) |
| start_time | timestamptz | NOT NULL | 开始时间 |
| end_time | timestamptz | NOT NULL | 结束时间 |
| status | varchar(20) | NOT NULL | 状态 |
| org_id | varchar(50) | FK | 适用组织ID (空则为全公司) |
| attendance_weight | smallint | NOT NULL | 出勤权重 (%) |
| leave_weight | smallint | NOT NULL | 请假权重 (%) |

#### 10. performance_evaluation (绩效评估结果表)
存储员工在特定周期的绩效评分。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | varchar(50) | PK | 主键 (UUID) |
| emp_id | varchar(50) | FK, NOT NULL | 被评估人ID |
| cycle_id | varchar(50) | FK, NOT NULL | 关联周期ID |
| final_score | numeric(10,2) | | 最终得分 |
| final_remark | text | | 最终评语 |
| evaluation_status | varchar(20) | NOT NULL | 评估状态 (自评中/评分中/已归档) |
| appeal_status | varchar(20) | NOT NULL | 申诉状态 |
| attendance_rate | numeric(6,4) | | 周期内出勤率 |
| leave_rate | numeric(6,4) | | 周期内请假率 |
| rule_score | numeric(10,2) | | 规则自动计算得分 |

### 2.4 审计模块

#### 11. hrms_audit (审计日志表)
记录系统关键数据的变更日志。

| 字段名 | 数据类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | bigint | PK, IDENTITY | 自增主键 |
| table_name | varchar(50) | | 操作表名 |
| record_id | varchar(200) | | 受影响记录ID |
| oper_type | varchar(20) | NOT NULL | 操作类型 (INSERT/UPDATE/DELETE) |
| summary | varchar(200) | | 操作摘要 |
| old_data | jsonb | | 变更前数据快照 |
| new_data | jsonb | | 变更后数据快照 |
| oper_user | varchar(32) | NOT NULL | 操作人账号 |
| oper_time | timestamptz | NOT NULL | 操作时间 |

---

## 3. 表之间的关系 (Entity Relationships)

### 3.1 组织与员工关系
*   **Organization 自关联**: `organization.parent_org_id` -> `organization.id`。
    *   **关系描述**: 构成树形组织结构，一个组织可以有父级组织。
*   **Organization 与 Employee (负责人)**: `organization.manager_emp_id` -> `employee.id`。
    *   **关系描述**: 一个组织可以指定一名员工为负责人。
*   **Employee 与 Organization (归属)**: `employee.org_id` -> `organization.id`。
    *   **关系描述**: 员工必须归属于一个组织（部门）。
*   **Employee 自关联 (汇报线)**: `employee.manager_emp_id` -> `employee.id`。
    *   **关系描述**: 员工可以有一个直属上级（也是员工）。
*   **Employee 与 EmployeeHistory**: `employee_history.emp_id` -> `employee.id`。
    *   **关系描述**: 一名员工可以有多条历史变更记录（一对多）。

### 3.2 考勤与请假关系
*   **Employee 与 Attendance**: `attendance.emp_id` -> `employee.id`。
    *   **关系描述**: 一名员工每天产生一条考勤记录（一对多）。
*   **Employee 与 LeaveApply**: `leave_apply.emp_id` -> `employee.id`。
    *   **关系描述**: 一名员工可以提交多份请假申请（一对多）。
*   **LeaveApply 与 LeaveTimeSegment**: `leave_time_segment.leave_id` -> `leave_apply.id`。
    *   **关系描述**: 一份请假申请可以包含多个时间段（例如跨周末请假可能被拆分），是一对多关系。
*   **Employee 与 LeaveTimeSegment**: `leave_time_segment.emp_id` -> `employee.id`。
    *   **关系描述**: 冗余关联，用于在数据库层面通过 `EXCLUDE` 约束防止同一员工的时间段重叠。

### 3.3 绩效关系
*   **Organization 与 PerformanceCycle**: `performance_cycle.org_id` -> `organization.id`。
    *   **关系描述**: 绩效周期可以针对特定部门设定，也可以为空（针对全公司）。
*   **Employee 与 PerformanceEvaluation**: `performance_evaluation.emp_id` -> `employee.id`。
    *   **关系描述**: 员工在每个周期内有一份评估记录。
*   **PerformanceCycle 与 PerformanceEvaluation**: `performance_evaluation.cycle_id` -> `performance_cycle.id`。
    *   **关系描述**: 一个绩效周期包含多名员工的评估记录（一对多）。
