-- 开启 btree_gist 扩展 (用于混合类型索引)
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- 为 LeaveTimeSegment 添加排除约束 (防止同一员工时间重叠)

ALTER TABLE leave_time_segment
ADD CONSTRAINT exclude_emp_leave_time
EXCLUDE USING gist (
    emp_id WITH =,
    tstzrange(leave_start_time, leave_end_time, '[]') WITH &&
);
