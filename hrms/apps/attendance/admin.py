from django.contrib import admin
from django.db import transaction

from .forms import AttendanceShiftForm
from .models import Attendance, AttendanceShift


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "emp",
        "attendance_date",
        "attendance_status",
        "check_in_time",
        "check_out_time",
    )
    list_filter = ("attendance_status", "attendance_date")
    search_fields = ("emp__emp_name", "emp__emp_id")
    readonly_fields = ("create_time", "update_time")


@admin.register(AttendanceShift)
class AttendanceShiftAdmin(admin.ModelAdmin):
    form = AttendanceShiftForm
    list_display = (
        "shift_name",
        "check_in_start_time",
        "check_in_end_time",
        "check_out_start_time",
        "check_out_end_time",
        "is_active",
        "update_time",
    )
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    ordering = ("-update_time",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "shift_name",
                    "check_in_start_time",
                    "check_in_end_time",
                    "check_out_start_time",
                    "check_out_end_time",
                    "is_active",
                ),
                "description": "配置打卡时间区间（12小时制），并勾选当前生效班次。",
            },
        ),
        (
            "轨迹信息",
            {
                "fields": ("create_time", "update_time", "create_by", "update_by"),
            },
        ),
    )
    readonly_fields = ("create_time", "update_time")
    actions = ("activate_shift",)

    def activate_shift(self, request, queryset):
        with transaction.atomic():
            AttendanceShift.objects.update(is_active=False)
            queryset.update(is_active=True)
        self.message_user(request, "已将选中的班次设为当前生效。")

    activate_shift.short_description = "设为当前班次（取消其他班次）"

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            with transaction.atomic():
                AttendanceShift.objects.exclude(pk=obj.pk).update(is_active=False)
                super().save_model(request, obj, form, change)
        else:
            super().save_model(request, obj, form, change)
