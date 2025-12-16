-- 通用更新时间触发器函数 (对应规则文档 3.1.2)
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
