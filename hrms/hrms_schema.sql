-- ==========================================
-- HRMS 核心业务数据库结构 (用于 E-R 图生成)
-- ==========================================

-- 1. 组织架构表
CREATE TABLE public.organization (
    id character varying(50) PRIMARY KEY,
    org_code character varying(50) UNIQUE NOT NULL,
    org_name character varying(100) NOT NULL,
    org_type character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    effective_time timestamp with time zone NOT NULL,
    expire_time timestamp with time zone,
    manager_emp_id character varying(50), -- FK to employee
    parent_org_id character varying(50),  -- FK to organization
    is_deleted boolean NOT NULL,
    create_time timestamp with time zone,
    update_time timestamp with time zone
);

-- 2. 员工表
CREATE TABLE public.employee (
    id character varying(50) PRIMARY KEY,
    emp_id character varying(32) UNIQUE NOT NULL,
    emp_name character varying(50) NOT NULL,
    id_card character varying(18) UNIQUE NOT NULL,
    gender character varying(10) NOT NULL,
    birth_date date NOT NULL,
    phone character varying(20) NOT NULL,
    email character varying(100) UNIQUE NOT NULL,
    hire_date date NOT NULL,
    "position" character varying(50) NOT NULL,
    employment_type character varying(20) NOT NULL,
    emp_status character varying(20) NOT NULL,
    manager_emp_id character varying(50), -- FK to employee
    org_id character varying(50) NOT NULL, -- FK to organization
    user_id integer UNIQUE, -- 关联 Django User
    is_deleted boolean NOT NULL,
    create_time timestamp with time zone,
    update_time timestamp with time zone
);

-- 3. 员工履历/变更记录表
CREATE TABLE public.employee_history (
    id character varying(50) PRIMARY KEY,
    emp_id character varying(50) NOT NULL, -- FK to employee
    field_name character varying(50) NOT NULL,
    old_value text,
    new_value text,
    change_reason character varying(200),
    create_time timestamp with time zone
);

-- 4. 考勤记录表
CREATE TABLE public.attendance (
    id character varying(50) PRIMARY KEY,
    emp_id character varying(50) NOT NULL, -- FK to employee
    attendance_date date NOT NULL,
    attendance_type character varying(20) NOT NULL,
    check_in_time timestamp with time zone,
    check_out_time timestamp with time zone,
    attendance_status character varying(20) NOT NULL,
    exception_reason text,
    appeal_status character varying(20) NOT NULL,
    is_deleted boolean NOT NULL
);

-- 5. 考勤班次配置表
CREATE TABLE public.attendance_shift (
    id character varying(50) PRIMARY KEY,
    shift_name character varying(64) NOT NULL,
    check_in_start_time time without time zone NOT NULL,
    check_in_end_time time without time zone NOT NULL,
    check_out_start_time time without time zone NOT NULL,
    check_out_end_time time without time zone NOT NULL,
    is_active boolean NOT NULL
);

-- 6. 请假申请表
CREATE TABLE public.leave_apply (
    id character varying(50) PRIMARY KEY,
    emp_id character varying(50) NOT NULL, -- FK to employee
    leave_type character varying(20) NOT NULL,
    apply_status character varying(20) NOT NULL,
    apply_time timestamp with time zone NOT NULL,
    reason text,
    attachment_url character varying(255),
    total_days numeric(10,2) NOT NULL,
    is_deleted boolean NOT NULL
);

-- 7. 请假时间段明细表
CREATE TABLE public.leave_time_segment (
    id character varying(50) PRIMARY KEY,
    leave_id character varying(50) NOT NULL, -- FK to leave_apply
    emp_id character varying(50) NOT NULL,   -- FK to employee
    leave_start_time timestamp with time zone NOT NULL,
    leave_end_time timestamp with time zone NOT NULL,
    segment_days numeric(10,2) NOT NULL,
    is_active boolean NOT NULL
);

-- 8. 请假类型配置表
CREATE TABLE public.config_leave_reason (
    id character varying(50) PRIMARY KEY,
    code character varying(32) UNIQUE NOT NULL,
    name character varying(64) NOT NULL,
    description text NOT NULL,
    max_days numeric(5,2) NOT NULL,
    requires_attachment boolean NOT NULL,
    status character varying(20) NOT NULL
);

-- 9. 绩效周期表
CREATE TABLE public.performance_cycle (
    id character varying(50) PRIMARY KEY,
    cycle_name character varying(100) NOT NULL,
    cycle_type character varying(20) NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    status character varying(20) NOT NULL,
    org_id character varying(50), -- FK to organization
    attendance_weight smallint NOT NULL,
    leave_weight smallint NOT NULL
);

-- 10. 绩效评估结果表
CREATE TABLE public.performance_evaluation (
    id character varying(50) PRIMARY KEY,
    emp_id character varying(50) NOT NULL, -- FK to employee
    cycle_id character varying(50) NOT NULL, -- FK to performance_cycle
    final_score numeric(10,2),
    final_remark text,
    evaluation_status character varying(20) NOT NULL,
    appeal_status character varying(20) NOT NULL,
    attendance_rate numeric(6,4),
    leave_rate numeric(6,4),
    rule_score numeric(10,2)
);

-- 11. 审计日志表
CREATE TABLE public.hrms_audit (
    id bigint PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    table_name character varying(50),
    record_id character varying(200),
    oper_type character varying(20) NOT NULL,
    summary character varying(200),
    old_data jsonb,
    new_data jsonb,
    oper_user character varying(32) NOT NULL,
    oper_time timestamp with time zone NOT NULL
);

-- ==========================================
-- 外键关系 (Relationships)
-- ==========================================

-- 员工 -> 组织
ALTER TABLE public.employee ADD CONSTRAINT fk_employee_org FOREIGN KEY (org_id) REFERENCES public.organization(id);
-- 员工 -> 员工 (汇报对象)
ALTER TABLE public.employee ADD CONSTRAINT fk_employee_manager FOREIGN KEY (manager_emp_id) REFERENCES public.employee(id);

-- 组织 -> 员工 (负责人)
ALTER TABLE public.organization ADD CONSTRAINT fk_org_manager FOREIGN KEY (manager_emp_id) REFERENCES public.employee(id);
-- 组织 -> 组织 (父级)
ALTER TABLE public.organization ADD CONSTRAINT fk_org_parent FOREIGN KEY (parent_org_id) REFERENCES public.organization(id);

-- 员工履历 -> 员工
ALTER TABLE public.employee_history ADD CONSTRAINT fk_history_emp FOREIGN KEY (emp_id) REFERENCES public.employee(id);

-- 考勤 -> 员工
ALTER TABLE public.attendance ADD CONSTRAINT fk_attendance_emp FOREIGN KEY (emp_id) REFERENCES public.employee(id);

-- 请假 -> 员工
ALTER TABLE public.leave_apply ADD CONSTRAINT fk_leave_emp FOREIGN KEY (emp_id) REFERENCES public.employee(id);

-- 请假明细 -> 请假申请
ALTER TABLE public.leave_time_segment ADD CONSTRAINT fk_segment_leave FOREIGN KEY (leave_id) REFERENCES public.leave_apply(id);
-- 请假明细 -> 员工
ALTER TABLE public.leave_time_segment ADD CONSTRAINT fk_segment_emp FOREIGN KEY (emp_id) REFERENCES public.employee(id);

-- 绩效周期 -> 组织
ALTER TABLE public.performance_cycle ADD CONSTRAINT fk_cycle_org FOREIGN KEY (org_id) REFERENCES public.organization(id);

-- 绩效评估 -> 员工
ALTER TABLE public.performance_evaluation ADD CONSTRAINT fk_eval_emp FOREIGN KEY (emp_id) REFERENCES public.employee(id);
-- 绩效评估 -> 绩效周期
ALTER TABLE public.performance_evaluation ADD CONSTRAINT fk_eval_cycle FOREIGN KEY (cycle_id) REFERENCES public.performance_cycle(id);

