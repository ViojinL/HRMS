from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Q
from apps.leave.models import LeaveApply
from apps.performance.models import PerformanceEvaluation
from apps.attendance.models import Attendance
from apps.audit.models import AuditLog
from apps.employee.models import Employee

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def _format_time(self, value, fmt='%H:%M'):
        if not value:
            return '--:--'
        return timezone.localtime(value).strftime(fmt)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        emp = getattr(user, 'employee', None)
        context['user_display_name'] = emp.emp_name if emp and emp.emp_name else user.username
        context['today_attendance_display'] = '--:--'
        
        # 1. 问候语时间段
        hour = timezone.now().hour
        if 5 <= hour < 12:
            greeting = '早上好'
        elif 12 <= hour < 14:
            greeting = '中午好'
        elif 14 <= hour < 19:
            greeting = '下午好'
        else:
            greeting = '晚上好'
        context['greeting'] = greeting

        # 特殊处理：超级管理员如果没有关联档案，显示系统概览
        if not emp:
            if user.is_superuser:
                # 获取系统级统计数据
                from apps.organization.models import Organization
                from django.contrib.auth.models import User as AuthUser
                
                context['is_admin_dashboard'] = True
                context['total_employees'] = Employee.objects.count()
                context['total_orgs'] = Organization.objects.count()
                context['active_users'] = AuthUser.objects.filter(is_active=True).count()
                
                # 获取全站最近动态
                context['recent_activities'] = AuditLog.objects.all().order_by('-oper_time')[:10]
                return context
            else:
                context['is_new_user'] = True
                return context

        # 2. 统计数据
        # 待办审批 (作为管理者，查询下属申请的待审批单据)
        # 逻辑：申请人的 manager 是我，且状态是 pending
        pending_approvals = LeaveApply.objects.filter(
            emp__manager_emp=emp, 
            apply_status='pending'
        ).count()
        is_manager = Employee.objects.filter(manager_emp=emp).exists()
        
        # 待办绩效评价 (自评 或 他评)
        pending_perf = PerformanceEvaluation.objects.filter(
            Q(emp=emp, evaluation_status='self_eval') | 
            Q(emp__manager_emp=emp, evaluation_status='manager_eval')
        ).count()
        
        
        context['total_todos'] = pending_approvals + pending_perf
        context['pending_approvals_count'] = pending_approvals
        context['show_pending_approvals'] = is_manager
        
        # 3. 今日考勤
        today = timezone.now().date()
        today_attendance = Attendance.objects.filter(emp=emp, attendance_date=today).first()
        context['today_attendance'] = today_attendance
        context['today_attendance_display'] = self._format_time(
            today_attendance.check_in_time if today_attendance else None
        )


        # 4. 我的最近申请
        leaves = list(LeaveApply.objects.filter(emp=emp).order_by('-create_time')[:5])
        for leave in leaves:
            leave.leave_type_label = leave.get_leave_type_display()
        context['recent_leaves'] = leaves

        # 5. 为了填充右侧动态，获取最近的公开操作或通知 (这里暂用自己的审计记录)
        context['recent_activities'] = AuditLog.objects.filter(oper_user=user.username).order_by('-oper_time')[:8]

        return context
