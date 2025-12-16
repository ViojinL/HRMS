import os
import django
import sys
from datetime import timedelta

# 设置环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.contrib.auth.models import User
from apps.employee.models import Employee
from apps.organization.models import Organization
from apps.leave.models import LeaveApply, LeaveTimeSegment
from apps.performance.models import PerformanceCycle, PerformanceEvaluation, PerformanceIndicatorSet
from django.utils import timezone

def create_org(code, name, type, parent=None, manager_emp=None):
    org, created = Organization.objects.get_or_create(
        org_code=code,
        defaults={
            'org_name': name,
            'org_type': type,
            'parent_org': parent,
            'effective_time': timezone.now(),  # Fix: effective_time is required
            'create_by': 'system',
            'update_by': 'system'
        }
    )
    if not created:
        # 如果已存在，更新父节点以确保树形结构
        org.parent_org = parent
        org.save()
        
    if manager_emp:
        org.manager_emp = manager_emp
        org.save()
    
    print(f"  [Org] {name} ({code}) checked.")
    return org

def create_user_emp(username, name, emp_id, org, position, manager=None, is_staff=False):
    # 1. User
    user, _ = User.objects.get_or_create(username=username, defaults={'email': f'{username}@hrms.com', 'is_staff': is_staff})
    user.set_password('password123')
    user.save()

    # 2. Employee
    defaults = {
        'id_card': f'42010119900101{emp_id[-4:]}',
        'emp_name': name,
        'gender': 'male',
        'birth_date': '1990-01-01',
        'phone': f'1380000{emp_id[-4:]}',
        'email': f'{username}@hrms.com',
        'hire_date': timezone.now(),
        'org': org,
        'position': position,
        'employment_type': 'full_time',
        'emp_status': 'active',
        'user': user,
        'manager_emp': manager,
        'create_by': 'system',
        'update_by': 'system'
    }
    
    emp, created = Employee.objects.get_or_create(emp_id=emp_id, defaults=defaults)
    if not created:
        # 更新汇报关系
        emp.manager_emp = manager
        emp.org = org
        emp.user = user
        emp.save()
    
    print(f"  [Emp] {name} - {position} created.")
    return emp

def init_full_structure():
    print("=== 开始构建组织架构树 ===")
    
    # 1. 根节点
    root = create_org('ROOT', '未来科技集团', 'company')
    
    # 2. 一级部门
    hr_dept = create_org('HR', '人力资源部', 'department', parent=root)
    tech_dept = create_org('TECH', '技术研发中心', 'department', parent=root)
    
    # 3. 二级团队
    fe_team = create_org('FE', '前端开发组', 'team', parent=tech_dept)
    be_team = create_org('BE', '后端开发组', 'team', parent=tech_dept)

    print("\n=== 开始录入人员 ===")
    
    # Level 1: CEO
    ceo = create_user_emp('ceo', '张总', 'E001', root, 'CEO', is_staff=True)
    root.manager_emp = ceo
    root.save()

    # Level 2: 部门总监
    hr_dir = create_user_emp('hr_dir', '李人资', 'E002', hr_dept, 'HR总监', manager=ceo, is_staff=True)
    hr_dept.manager_emp = hr_dir
    hr_dept.save()

    tech_dir = create_user_emp('tech_dir', '王技术', 'E003', tech_dept, '技术总监', manager=ceo)
    tech_dept.manager_emp = tech_dir
    tech_dept.save()

    # Level 3: 团队Leader
    fe_lead = create_user_emp('fe_lead', '赵前端', 'E004', fe_team, '前端组长', manager=tech_dir)
    fe_team.manager_emp = fe_lead
    fe_team.save()

    be_lead = create_user_emp('be_lead', '孙后端', 'E005', be_team, '后端组长', manager=tech_dir)
    be_team.manager_emp = be_lead
    be_team.save()

    # Level 4: 基层员工
    emp1 = create_user_emp('dev001', '周杰伦', 'E006', fe_team, '高级前端', manager=fe_lead)
    emp2 = create_user_emp('dev002', '林俊杰', 'E007', be_team, '高级后端', manager=be_lead)
    emp3 = create_user_emp('dev003', '陶喆', 'E008', be_team, '初级后端', manager=be_lead)

    print("\n=== 初始化业务数据 (绩效/请假) ===")
    
    # 创建绩效周期
    cycle, _ = PerformanceCycle.objects.get_or_create(
        cycle_name='2024年Q4全员考核',
        defaults={
            'cycle_type': 'quarterly', 
            'status': 'in_progress',
            'start_time': timezone.now(), 
            'end_time': timezone.now() + timedelta(days=30),
            'create_by': str(hr_dir.user.id),
            'update_by': str(hr_dir.user.id)
        }
    )

    # 创建指标集
    kpi_set, _ = PerformanceIndicatorSet.objects.get_or_create(
        set_name='研发通用KPI',
        cycle=cycle,
        defaults={'total_weight': 100, 'create_by': str(hr_dir.user.id), 'update_by': str(hr_dir.user.id)}
    )

    # 为所有技术部员工分配绩效
    for emp in [tech_dir, fe_lead, be_lead, emp1, emp2, emp3]:
        PerformanceEvaluation.objects.get_or_create(
            cycle=cycle, emp=emp,
            defaults={
                'indicator_set': kpi_set,
                'evaluation_status': 'self_eval',
                'create_by': str(hr_dir.user.id),
                'update_by': str(hr_dir.user.id)
            }
        )
    
    print("数据初始化完成。")
    print("推荐测试账号：")
    print("1. CEO (ceo/password123) - 可视全公司")
    print("2. 技术总监 (tech_dir/password123) - 可视所有技术人员")
    print("3. 后端组长 (be_lead/password123) - 可视后端组员")

if __name__ == '__main__':
    try:
        init_full_structure()
    except Exception as e:
        print(f"Error: {e}")
