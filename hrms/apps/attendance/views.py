from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import View
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from datetime import time
from types import SimpleNamespace
from .forms import AttendanceShiftSettingsForm
from .models import Attendance, AttendanceShift

class AttendanceShiftSettingsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'attendance/shift_settings.html'
    form_class = AttendanceShiftSettingsForm
    success_url = reverse_lazy('attendance:shift_settings')
    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff

    def get_selected_shift(self):
        if hasattr(self, '_selected_shift') and self._selected_shift is not None:
            return self._selected_shift
        shift_id = self.request.GET.get('shift_id')
        shift = None
        if shift_id:
            shift = AttendanceShift.objects.filter(pk=shift_id).first()
        if not shift:
            shift = AttendanceShift.get_active_shift()
        self._selected_shift = shift
        return shift

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        shift = self.get_selected_shift()
        if shift:
            kwargs['instance'] = shift
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_shift'] = self.get_selected_shift()
        context['shifts'] = AttendanceShift.objects.order_by('-update_time')
        return context

    def form_valid(self, form):
        shift = form.save(commit=False)
        shift.is_active = True
        shift.update_by = str(self.request.user.id)
        if not shift.pk:
            shift.create_by = str(self.request.user.id)
        shift.save()
        AttendanceShift.objects.exclude(pk=shift.pk).update(is_active=False)
        self._selected_shift = shift
        messages.success(self.request, f'班次“{shift.shift_name}”已设为当前待打卡时间。')
        return super().form_valid(form)

STATUS_BADGE_CLASSES = {
    'normal': 'bg-green-500',
    'late': 'bg-yellow-500',
    'early_leave': 'bg-orange-500',
    'absent': 'bg-red-500',
    'leave': 'bg-blue-500',
    'field': 'bg-purple-500',
    'overtime': 'bg-cyan-500',
}
STATUS_DISPLAY_MAP = dict(Attendance.STATUS_CHOICES)

class AttendanceDashboardView(LoginRequiredMixin, View):
    template_name = 'attendance/dashboard.html'

    def _format_time(self, dt):
        if not dt:
            return '--'
        return timezone.localtime(dt).strftime('%H:%M:%S')

    def _status_dot_class(self, status):
        return STATUS_BADGE_CLASSES.get(status, 'bg-red-500')

    def _get_shift(self):
        shift = AttendanceShift.get_active_shift()
        if shift:
            return shift
        return SimpleNamespace(
            shift_name='默认班次',
            check_in_start_time=time(9, 0),
            check_in_end_time=time(9, 30),
            check_out_start_time=time(17, 30),
            check_out_end_time=time(18, 0),
        )

    def _to_local_time(self, dt):
        if not dt:
            return None
        return timezone.localtime(dt).time()

    def _is_late_time(self, dt, shift):
        current = self._to_local_time(dt)
        if not current:
            return False
        return current > shift.check_in_end_time

    def _is_early_leave_time(self, dt, shift):
        current = self._to_local_time(dt)
        if not current:
            return False
        return current < shift.check_out_start_time

    def _determine_status_key(self, record, shift):
        status = record.attendance_status
        if status == 'normal':
            if self._is_late_time(record.check_in_time, shift):
                return 'late'
            if self._is_early_leave_time(record.check_out_time, shift):
                return 'early_leave'
        return status

    def _status_label(self, status_key):
        return STATUS_DISPLAY_MAP.get(status_key, '异常')

    def get(self, request):
        today = timezone.localtime(timezone.now()).date()
        user_emp = getattr(request.user, 'employee', None)
        if not user_emp:
            messages.error(request, "未绑定员工档案，无法打卡")
            return redirect('login')

        shift = self._get_shift()
        today_record = Attendance.objects.filter(emp=user_emp, attendance_date=today).first()
        current_month = list(Attendance.objects.filter(
            emp=user_emp,
            attendance_date__month=today.month,
            attendance_date__year=today.year
        ).order_by('attendance_date'))

        today_record_data = None
        if today_record:
            status_key = self._determine_status_key(today_record, shift)
            today_record_data = {
                'check_in_display': self._format_time(today_record.check_in_time),
                'check_out_display': self._format_time(today_record.check_out_time),
                'status_label': self._status_label(status_key),
                'is_normal': status_key == 'normal',
                'status_dot_class': self._status_dot_class(status_key),
                'attendance_status': status_key,
                'status_key': status_key,
                'has_check_in': bool(today_record.check_in_time),
                'has_check_out': bool(today_record.check_out_time),
            }

        current_month_records = []
        for record in current_month:
            status_key = self._determine_status_key(record, shift)
            current_month_records.append({
                'date_label': record.attendance_date.strftime('%m-%d'),
                'weekday_label': record.attendance_date.strftime('%a'),
                'check_in_display': self._format_time(record.check_in_time),
                'check_out_display': self._format_time(record.check_out_time),
                'status_label': self._status_label(status_key),
                'status_dot_class': self._status_dot_class(status_key),
                'status_key': status_key,
                'show_appeal': status_key != 'normal',
            })

        context = {
            'today': today,
            'today_record': today_record_data,
            'current_month_records': current_month_records,
            'shift': shift,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """处理打卡请求"""
        user_emp = getattr(request.user, 'employee', None)
        shift = self._get_shift()
        now_utc = timezone.now()
        now_local = timezone.localtime(now_utc)
        today = now_local.date()
        now_local_time = now_local.time()
        is_morning = now_local_time < time(12, 0, 0)

        attendance, created = Attendance.objects.get_or_create(
            emp=user_emp,
            attendance_date=today,
            defaults={
                'attendance_type': 'check_in',
                'attendance_status': 'normal',
                'create_by': str(request.user.id),
                'update_by': str(request.user.id)
            }
        )

        msg = ""
        status = 'normal'

        if is_morning:
            if attendance.check_in_time:
                messages.warning(request, "未到时间，无法再次签到")
                return redirect('attendance:dashboard')

            attendance.check_in_time = now_utc
            if now_local_time > shift.check_in_end_time:
                status = 'late'
                msg = "打卡成功，但您迟到了"
            else:
                msg = "签到成功，早安！"
        else:
            if attendance.check_out_time:
                messages.warning(request, "今日已签退，无需重复打卡")
                return redirect('attendance:dashboard')

            attendance.check_out_time = now_utc
            if now_local_time < shift.check_out_start_time:
                status = 'early_leave' if attendance.attendance_status != 'late' else 'late'
                msg = "签退成功，注意早退"
            else:
                msg = "签退成功，辛苦了！"

        if attendance.attendance_status == 'normal' and status != 'normal':
            attendance.attendance_status = status

        attendance.save()
        messages.success(request, msg)
        return redirect('attendance:dashboard')
