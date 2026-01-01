-- Common reporting/search views for HRMS (raw SQL)

-- Employee profile view (includes org + direct manager)
DROP VIEW IF EXISTS vw_employee_profile;
CREATE VIEW vw_employee_profile AS
SELECT
    emp.id AS emp_pk,
    emp.emp_id,
    emp.emp_name,
    emp.gender,
    emp.birth_date,
    emp.phone,
    emp.email,
    emp.hire_date,
    emp.position,
    emp.employment_type,
    emp.emp_status,
    emp.id_card,
    emp.user_id,
    emp.manager_emp_id,
    mgr.emp_id AS manager_emp_code,
    mgr.emp_name AS manager_emp_name,
    org.id AS org_id,
    org.org_code,
    org.org_name,
    org.parent_org_id
FROM employee emp
JOIN organization org ON emp.org_id = org.id
LEFT JOIN employee mgr ON emp.manager_emp_id = mgr.id
WHERE emp.is_deleted = FALSE
  AND org.is_deleted = FALSE;


-- Leave profile view (includes employee + org + aggregated segments)
DROP VIEW IF EXISTS vw_leave_profile;
CREATE VIEW vw_leave_profile AS
SELECT
    la.id AS leave_id,
    la.leave_type,
    la.apply_status,
    la.total_days,
    la.apply_time,
    la.reason,
    emp.id AS emp_pk,
    emp.emp_id,
    emp.emp_name,
    org.id AS org_id,
    org.org_code,
    org.org_name,
    seg.start_time,
    seg.end_time
FROM leave_apply la
JOIN employee emp ON la.emp_id = emp.id
JOIN organization org ON emp.org_id = org.id
LEFT JOIN (
    SELECT
        leave_id,
        MIN(leave_start_time) AS start_time,
        MAX(leave_end_time) AS end_time
    FROM leave_time_segment
    WHERE is_deleted = FALSE
    GROUP BY leave_id
) seg ON seg.leave_id = la.id
WHERE la.is_deleted = FALSE
  AND emp.is_deleted = FALSE
  AND org.is_deleted = FALSE;
