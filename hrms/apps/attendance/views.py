from django.shortcuts import render, redirect
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time
from .models import Attendance

class AttendanceDashboardView(LoginRequiredMixin, View):
    template_name = 'attendance/dashboard.html'
    
    def get(self, request):
        today = timezone.now().date()
        user_emp = getattr(request.user, 'employee', None)
        
        if not user_emp:
            messages.error(request, "未绑定员工档案，无法打卡")
            return redirect('login')

        # 获取今日考勤记录
        today_record = Attendance.objects.filter(emp=user_emp, attendance_date=today).first()
        
        # 获取本月考勤记录 (用于日历展示)
        current_month = list(Attendance.objects.filter(
            emp=user_emp, 
            attendance_date__month=today.month,
            attendance_date__year=today.year
        ).order_by('attendance_date'))
        
        context = {
            'today': today,
            'today_record': today_record,
            'current_month_records': current_month,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """处理打卡请求"""
        user_emp = getattr(request.user, 'employee', None)
        now = timezone.now()
        today = now.date()
        
        # 简单规则：12:00前为签到，12:00后为签退（仅作演示，实际应支持多次打卡或配置）
        is_morning = now.time() < time(12, 0, 0)
        
        attendance, created = Attendance.objects.get_or_create(
            emp=user_emp,
            attendance_date=today,
            defaults={
                'attendance_type': 'check_in',
                'attendance_status': 'normal', # 默认正常，稍后更新
                'create_by': str(request.user.id),
                'update_by': str(request.user.id)
            }
        )
        
        msg = ""
        status = 'normal'
        
        if is_morning:
            if attendance.check_in_time:
                messages.warning(request, "今日已签到，无需重复打卡")
                return redirect('attendance:dashboard')
            
            attendance.check_in_time = now
            # 迟到判断 (假设9:00上班)
            if now.time() > time(9, 0, 0):
                status = 'late'
                msg = "打卡成功，但您迟到了"
            else:
                msg = "签到成功，早安！"
        else:
            if attendance.check_out_time:
                messages.warning(request, "今日已签退，无需重复打卡")
                return redirect('attendance:dashboard')
            
            attendance.check_out_time = now
            # 早退判断 (假设18:00下班)
            if now.time() < time(18, 0, 0):
                status = 'early_leave' if attendance.attendance_status != 'late' else 'late' # 如果早上迟到，保持迟到状态或双重异常
                msg = "签退成功，注意早退"
            else:
                msg = "签退成功，辛苦了！"
                
        # 更新状态 (简单逻辑：只有当状态比当前更严重时才更新，或者覆盖正常)
        if attendance.attendance_status == 'normal' and status != 'normal':
             attendance.attendance_status = status
             
        attendance.save()
        messages.success(request, msg)
        return redirect('attendance:dashboard')
