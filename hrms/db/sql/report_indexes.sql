-- Indexes to speed up common HRMS queries (PostgreSQL)
-- Safe to run multiple times.

-- Employee: frequent filters/sorts
CREATE INDEX IF NOT EXISTS idx_employee_org_id ON employee (org_id);
CREATE INDEX IF NOT EXISTS idx_employee_emp_status ON employee (emp_status);
CREATE INDEX IF NOT EXISTS idx_employee_org_status ON employee (org_id, emp_status);
CREATE INDEX IF NOT EXISTS idx_employee_emp_id ON employee (emp_id);
CREATE INDEX IF NOT EXISTS idx_employee_manager_emp_id ON employee (manager_emp_id);
CREATE INDEX IF NOT EXISTS idx_employee_hire_date ON employee (hire_date);
CREATE INDEX IF NOT EXISTS idx_employee_birth_date ON employee (birth_date);

-- Optional: case-insensitive text searches (requires pg_trgm)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE INDEX IF NOT EXISTS idx_employee_emp_name_trgm ON employee USING gin (emp_name gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_employee_position_trgm ON employee USING gin (position gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_employee_email_trgm ON employee USING gin (email gin_trgm_ops);

-- Organization tree traversal
CREATE INDEX IF NOT EXISTS idx_organization_parent_org_id ON organization (parent_org_id);
CREATE INDEX IF NOT EXISTS idx_organization_manager_emp_id ON organization (manager_emp_id);

-- Leave: frequent filters
CREATE INDEX IF NOT EXISTS idx_leave_apply_emp_id ON leave_apply (emp_id);
CREATE INDEX IF NOT EXISTS idx_leave_apply_status ON leave_apply (apply_status);
CREATE INDEX IF NOT EXISTS idx_leave_apply_type ON leave_apply (leave_type);
CREATE INDEX IF NOT EXISTS idx_leave_apply_emp_status ON leave_apply (emp_id, apply_status);

-- Leave time segments: aggregation + overlap checks
CREATE INDEX IF NOT EXISTS idx_leave_time_segment_leave_id ON leave_time_segment (leave_id);
CREATE INDEX IF NOT EXISTS idx_leave_time_segment_emp_id ON leave_time_segment (emp_id);
CREATE INDEX IF NOT EXISTS idx_leave_time_segment_leave_start_time ON leave_time_segment (leave_start_time);
CREATE INDEX IF NOT EXISTS idx_leave_time_segment_leave_end_time ON leave_time_segment (leave_end_time);
CREATE INDEX IF NOT EXISTS idx_leave_time_segment_leave_range ON leave_time_segment (leave_id, leave_start_time, leave_end_time);
