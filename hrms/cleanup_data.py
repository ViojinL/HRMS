import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.organization.models import Organization
from apps.employee.models import Employee

def cleanup_data():
    print("=== 开始精准清理脏数据 ===")
    
    # 1. 精准定位要删除的员工 (EMP-1001)
    target_emp_code = 'EMP-1001'
    emps = Employee.objects.filter(emp_id=target_emp_code)
    
    if emps.exists():
        for emp in emps:
            print(f"找到旧员工: {emp.emp_name} ({emp.emp_id}) -> 正在删除及其关联数据...")
            # 删除员工会自动级联删除其 User (如果设置了 cascade) 或者需要手动处理
            # 我们的 Employee 模型是 on_delete=models.SET_NULL for user, so User remains.
            # 但这里我们只删 Employee 记录即可解除对 Organization 的引用
            emp.delete()
    else:
        print(f"未找到旧员工 {target_emp_code}，跳过。")

    # 2. 精准定位要删除的组织 (DEP-001)
    target_org_code = 'DEP-001'
    orgs = Organization.objects.filter(org_code=target_org_code)
    
    if orgs.exists():
        for org in orgs:
            print(f"找到旧组织: {org.org_name} ({org.org_code}) -> 正在删除...")
            try:
                org.delete()
                print("删除成功。")
            except Exception as e:
                print(f"删除失败: {e} (可能仍有其他关联数据)")
    else:
        print(f"未找到旧组织 {target_org_code}，跳过。")

    print("\n=== 清理结束 ===")
    print("现在请刷新组织架构页面，应该只剩下一棵完整的树了。")

if __name__ == '__main__':
    cleanup_data()
