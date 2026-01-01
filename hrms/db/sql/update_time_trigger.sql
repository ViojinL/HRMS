
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 绑定触发器到 Organization 表
CREATE TRIGGER trigger_organization_update_time
BEFORE UPDATE ON organization
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

-- 绑定触发器到 Employee 表
CREATE TRIGGER trigger_employee_update_time
BEFORE UPDATE ON employee
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();
