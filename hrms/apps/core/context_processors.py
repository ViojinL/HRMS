from apps.organization.models import Organization
from .roles import is_performance_admin


def user_roles(request):
    """
    全局上下文处理器：注入用户角色信息，用于前端菜单控制
    """
    context = {
        "is_manager": False,
        "is_hr": False,
        "is_admin": False,
        "is_performance_admin": False,
    }

    if not request.user.is_authenticated:
        return context

    # 1. 管理员
    if request.user.is_superuser:
        context["is_admin"] = True
        context["is_hr"] = True  # 管理员默认拥有HR视角
        context["is_manager"] = True  # 管理员默认拥有经理视角
        context["is_performance_admin"] = True
        return context

    # 2. 检查关联员工
    if hasattr(request.user, "employee"):
        emp = request.user.employee

        # 判断是否是部门负责人
        # 查找是否有任何组织将该员工设为 manager
        if Organization.objects.filter(manager_emp=emp).exists():
            context["is_manager"] = True

        # 判断是否是 HR (简单逻辑：所属部门名称包含'人力'或'HR'，或者职位包含'HR')
        # 实际项目中应使用更严谨的 Group 或 Role 表
        if "人力" in emp.org.org_name or "HR" in emp.position.upper():
            context["is_hr"] = True

        if request.user.is_staff:  # Django Staff 也可以视为 HR/后台人员
            context["is_hr"] = True

        context["is_performance_admin"] = is_performance_admin(request.user)

    return context
