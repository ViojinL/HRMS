from django.shortcuts import render, redirect, get_object_or_404, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View, DetailView
from django.db import transaction, IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .models import LeaveApply, LeaveTimeSegment
from .forms import LeaveApplyForm
from apps.employee.models import Employee
from django.utils import timezone
from decimal import Decimal

# ... (Existing imports: LeaveListView, LeaveApplyView) ...

class LeaveListView(LoginRequiredMixin, ListView):
    model = LeaveApply
    template_name = 'leave/list.html'
    context_object_name = 'leaves'

    def get_queryset(self):
        if not hasattr(self.request.user, 'employee'):
            return LeaveApply.objects.none()
        return LeaveApply.objects.filter(emp=self.request.user.employee).order_by('-create_time')

class LeaveApplyView(LoginRequiredMixin, View):
    def get(self, request):
        form = LeaveApplyForm()
        return render(request, 'leave/apply.html', {'form': form})

    def post(self, request):
        if hasattr(request.user, 'employee'):
            employee = request.user.employee
        else:
            messages.error(request, "系统未配置员工档案，无法提交")
            return redirect('leave:list')
        
        form = LeaveApplyForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    start_time = form.cleaned_data['start_time']
                    end_time = form.cleaned_data['end_time']
                    
                    duration = end_time - start_time
                    days = Decimal(duration.total_seconds() / (24 * 3600)).quantize(Decimal('0.01'))

                    leave = form.save(commit=False)
                    leave.emp = employee
                    leave.total_days = days
                    leave.create_by = request.user.id
                    leave.update_by = request.user.id
                    leave.save()

                    LeaveTimeSegment.objects.create(
                        leave=leave,
                        emp=employee,
                        leave_start_time=start_time,
                        leave_end_time=end_time,
                        segment_days=days,
                        create_by=request.user.id,
                        update_by=request.user.id
                    )
                
                messages.success(request, '请假申请已提交')
                return redirect('leave:list')
            except IntegrityError as e:
                if 'exclude_emp_leave_time' in str(e):
                    messages.error(request, '提交失败：该时间段内已有请假记录（数据库级拦截）')
                else:
                    messages.error(request, f'数据库错误：{str(e)}')
            except Exception as e:
                messages.error(request, f'系统错误：{str(e)}')
        
        return render(request, 'leave/apply.html', {'form': form})

class LeaveApprovalListView(LoginRequiredMixin, ListView):
    """
    待办审批列表
    逻辑：查找申请人的直属上级是当前用户的所有 待审批(pending) 记录
    """
    model = LeaveApply
    template_name = 'leave/approval_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        if not hasattr(self.request.user, 'employee'):
            return LeaveApply.objects.none()
        
        current_emp = self.request.user.employee
        # 查找所有汇报给当前员工的下属
        subordinates = Employee.objects.filter(manager_emp=current_emp)
        
        # 查找下属的待审批请求
        return LeaveApply.objects.filter(
            emp__in=subordinates, 
            apply_status='pending'
        ).select_related('emp').order_by('create_time')

class LeaveDetailView(LoginRequiredMixin, DetailView):
    model = LeaveApply
    template_name = 'leave/detail.html'
    context_object_name = 'leave'

    def get_object(self):
        obj = super().get_object()
        # 权限校验：只能看自己的，或者自己是审批人（上级）
        current_user = self.request.user
        if not hasattr(current_user, 'employee'):
            raise PermissionDenied
        
        current_emp = current_user.employee
        is_owner = obj.emp == current_emp
        is_manager = obj.emp.manager_emp == current_emp
        
        if not (is_owner or is_manager or current_user.is_superuser):
             raise PermissionDenied
        return obj

class LeaveActionView(LoginRequiredMixin, View):
    """
    审批动作：通过/拒绝
    """
    def post(self, request, pk):
        leave = get_object_or_404(LeaveApply, pk=pk)
        action = request.POST.get('action')
        
        # 权限校验
        if not hasattr(request.user, 'employee'):
             messages.error(request, "无权操作")
             return redirect('leave:list')

        current_emp = request.user.employee
        if leave.emp.manager_emp != current_emp and not request.user.is_superuser:
            messages.error(request, "您不是该申请的审批人")
            return redirect('leave:list')

        if action == 'approve':
            leave.apply_status = 'approved' # 简化流程：直接批准
            messages.success(request, '已批准该申请')
        elif action == 'reject':
            leave.apply_status = 'rejected'
            messages.success(request, '已拒绝该申请')
        else:
            messages.warning(request, '无效的操作')
            
        leave.update_by = request.user.id
        leave.save()
        return redirect('leave:approval_list')
