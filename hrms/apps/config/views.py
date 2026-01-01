from typing import Any, Dict
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView

from apps.attendance.models import AttendanceShift


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    request: HttpRequest  # runtime attribute provided by Django CBV

    def test_func(self) -> bool:
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "需要管理员权限才能访问此页面")
        return redirect('core:dashboard')


class ConfigHomeView(AdminRequiredMixin, TemplateView):
    template_name = 'config/home.html'

    def _get_count(self, model):
        try:
            return model.objects.count()
        except Exception:
            return 0

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'shifts': self._get_count(AttendanceShift),
        }
        context['sections'] = [
            {
                'title': '考勤规则',
                'items': [
                    {
                        'name': '班次/打卡窗口',
                        'desc': '上班/下班时间、弹性窗口，迟到早退判定的基础数据',
                        'url_name': 'attendance:shift_settings',
                        'status': 'available',
                    },
                ],
            },
            {
                'title': '请假规则',
                'items': [
                    {
                        'name': '请假理由与时长上限',
                        'desc': '统一使用系统内置请假类型（models.py）；参数化规则配置（规划中）',
                        'url_name': None,
                        'status': 'planned',
                    },
                    {
                        'name': '审批SLA与额度',
                        'desc': '审批时限、年假/调休额度、超时提醒（规划中）',
                        'url_name': None,
                        'status': 'planned',
                    },
                ],
            },
            {
                'title': '绩效规则',
                'items': [
                    {
                        'name': '周期模板与指标集',
                        'desc': '周期类型、时间、权重校验、指标集（规划中）',
                        'url_name': None,
                        'status': 'planned',
                    },
                ],
            },
            {
                'title': '安全与审计',
                'items': [
                    {
                        'name': '操作审计',
                        'desc': '查看系统审计日志，满足合规留痕',
                        'url_name': 'audit:list',
                        'status': 'available',
                    },
                    {
                        'name': '备份与恢复',
                        'desc': '数据库备份、恢复（规划中）',
                        'url_name': None,
                        'status': 'planned',
                    },
                ],
            },
        ]
        return context
