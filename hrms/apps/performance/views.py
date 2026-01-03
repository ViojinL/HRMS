from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    TemplateView,
    View,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import connection
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence, cast
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.http import HttpRequest
from .models import PerformanceCycle, PerformanceEvaluation
from .forms import PerformanceCycleForm, PerformanceAdminEvaluationForm
from apps.employee.models import Employee
from apps.organization.models import Organization
from .services import refresh_metrics_for_queryset, refresh_evaluation_metrics


class PerformanceAdminRequiredMixin(UserPassesTestMixin):
    """绩效管理权限：CFO/绩效部门/超级管理员。"""

    # Hint for Pylance: views mixins get request from Django CBV
    request: HttpRequest

    def test_func(self) -> bool:
        request = cast(HttpRequest, self.request)
        user = cast(AbstractUser | AnonymousUser, request.user)
        if user.is_superuser:
            return True
        emp = getattr(user, "employee", None)
        if not emp:
            return False
        position = (emp.position or "").upper()
        org_name = (getattr(emp.org, "org_name", "") or "").upper()
        return (
            position == "CFO"
            or "绩效" in (emp.position or "")
            or "绩效" in (getattr(emp.org, "org_name", "") or "")
            or "PERFORMANCE" in position
            or "PERFORMANCE" in org_name
        )


class PerformanceDashboardView(LoginRequiredMixin, ListView):
    template_name = "performance/dashboard.html"
    context_object_name = "cycles"

    def get_queryset(self):
        # 展示所有开启的绩效周期
        return PerformanceCycle.objects.filter(
            status__in=["in_progress", "not_started"]
        ).order_by("-start_time")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = cast(HttpRequest, self.request)
        user = cast(AbstractUser | AnonymousUser, request.user)
        emp = getattr(user, "employee", None)
        if emp:
            # 查找我的评估记录
            ctx["my_evaluations"] = PerformanceEvaluation.objects.filter(
                emp=emp
            ).select_related("cycle")
            refresh_metrics_for_queryset(ctx["my_evaluations"], save=True)

        cycles: Sequence[PerformanceCycle] = cast(
            Sequence[PerformanceCycle], ctx.get("cycles") or []
        )
        for cycle in cycles:
            cycle_any = cast(Any, cycle)
            cycle_any.cycle_type_label = cast(Any, cycle).get_cycle_type_display()
            cycle_any.status_label = cast(Any, cycle).get_status_display()
        ctx["status_choices"] = PerformanceCycle.STATUS_CHOICES
        return ctx


class PerformanceCycleCreateView(
    LoginRequiredMixin, PerformanceAdminRequiredMixin, CreateView
):
    # 仅CFO/绩效部门/管理员可用
    model = PerformanceCycle
    form_class = PerformanceCycleForm
    template_name = "performance/cycle_form.html"
    success_url = reverse_lazy("performance:dashboard")

    # Pylance hint for CBV-created attribute
    object: PerformanceCycle

    def form_valid(self, form):
        form.instance.create_by = self.request.user.username
        form.instance.update_by = self.request.user.username
        response = super().form_valid(form)

        cycle = cast(PerformanceCycle, self.object)
        employees = (
            Employee.objects.filter(org=cycle.org)
            if getattr(cycle, "org_id", None)
            else Employee.objects.all()
        )

        created = 0
        for emp in employees:
            PerformanceEvaluation.objects.get_or_create(
                cycle=cycle,
                emp=emp,
                defaults={
                    "evaluation_status": "not_started",
                    "appeal_status": "none",
                    "create_by": self.request.user.username,
                    "update_by": self.request.user.username,
                },
            )
            created += 1

        messages.success(
            self.request, f"绩效周期已创建，并初始化了 {created} 名员工的评估记录。"
        )
        return response


class PerformanceCycleDeleteView(
    LoginRequiredMixin, PerformanceAdminRequiredMixin, DeleteView
):
    """删除绩效周期。"""

    model = PerformanceCycle
    success_url = reverse_lazy("performance:dashboard")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "绩效周期及其关联的评估记录已删除。")
        return super().delete(request, *args, **kwargs)


class MyEvaluationListView(LoginRequiredMixin, ListView):
    template_name = "performance/my_list.html"
    context_object_name = "evaluations"

    def get_queryset(self):
        request = cast(HttpRequest, self.request)
        user = cast(AbstractUser | AnonymousUser, request.user)
        emp = getattr(user, "employee", None)
        if not emp:
            return PerformanceEvaluation.objects.none()
        qs = PerformanceEvaluation.objects.filter(emp=emp).select_related("cycle")
        refresh_metrics_for_queryset(qs, save=True)
        return qs


class PerformanceEvaluationManageListView(
    LoginRequiredMixin, PerformanceAdminRequiredMixin, ListView
):
    """绩效部门统一管理：评估列表。"""

    template_name = "performance/manage_list.html"
    context_object_name = "evaluations"

    def get_queryset(self):
        qs = PerformanceEvaluation.objects.select_related("cycle", "emp").order_by(
            "-cycle__start_time", "emp__emp_name"
        )
        refresh_metrics_for_queryset(qs, save=True)
        return qs


class PerformanceEvaluationManageUpdateView(
    LoginRequiredMixin, PerformanceAdminRequiredMixin, UpdateView
):
    """绩效部门统一管理：编辑评估（评分/状态/评价）。"""

    model = PerformanceEvaluation
    form_class = PerformanceAdminEvaluationForm
    template_name = "performance/manage_edit.html"
    success_url = reverse_lazy("performance:manage_list")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        refresh_evaluation_metrics(self.object, save=False)
        self.object.save()
        messages.success(self.request, "评估已更新")
        return super().form_valid(form)


class PerformanceCycleStatusUpdateView(
    LoginRequiredMixin, PerformanceAdminRequiredMixin, View
):
    """允许在仪表盘直接修改周期状态，并批量同步评估状态。"""

    eval_status_map = {
        "not_started": "not_started",
        "in_progress": "hr_audit",
        "ended": "completed",
        "archived": "completed",
    }

    def post(self, request, pk):
        cycle = get_object_or_404(PerformanceCycle, pk=pk, is_deleted=False)
        new_status = request.POST.get("status")
        valid_status = dict(PerformanceCycle.STATUS_CHOICES)

        if new_status not in valid_status:
            messages.error(request, "非法的状态值，未保存。")
            return redirect("performance:dashboard")

        cycle.status = new_status
        cycle.update_by = request.user.username
        cycle.save(update_fields=["status", "update_by", "update_time"])

        target_eval_status = self.eval_status_map.get(new_status)
        if target_eval_status:
            now = timezone.now()
            PerformanceEvaluation.objects.filter(cycle=cycle, is_deleted=False).update(
                evaluation_status=target_eval_status,
                update_by=request.user.username,
                update_time=now,
            )

        messages.success(
            request,
            f"周期状态已更新为“{valid_status[new_status]}”，相关评估状态已同步。",
        )
        return redirect("performance:dashboard")


class PerformanceSearchView(
    LoginRequiredMixin, PerformanceAdminRequiredMixin, TemplateView
):
    """绩效部门：原生 SQL 高级查找（按部门/时间/用户）。"""

    template_name = "performance/search.html"
    max_rows = 200

    def _parse_date(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None

        # 将用户输入的本地时间转换为带时区的时间，避免与数据库 UTC 比较产生错位
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        org_id = self.request.GET.get("org") or None
        start_str = self.request.GET.get("start") or None
        end_str = self.request.GET.get("end") or None
        keyword = (self.request.GET.get("keyword") or "").strip()

        start_dt = self._parse_date(start_str)
        end_dt_raw = self._parse_date(end_str)
        end_dt = end_dt_raw
        # 仅在用户只填日期（无时间）时，将结束日期扩展到当天 23:59:59
        if end_dt_raw and end_str and ("T" not in end_str and " " not in end_str):
            end_dt = end_dt_raw + timedelta(days=1) - timedelta(microseconds=1)
        # datetime-local 无秒，默认落在该分钟的 00 秒，可能漏掉 00-59 秒；向后补齐一整分钟
        elif end_dt_raw and end_dt_raw.second == 0 and end_dt_raw.microsecond == 0:
            end_dt = end_dt_raw + timedelta(seconds=59, microseconds=999999)

        clauses = [
            "ev.is_deleted = FALSE",
            "c.is_deleted = FALSE",
            "emp.is_deleted = FALSE",
        ]
        params: list[Any] = []

        if org_id:
            clauses.append("emp.org_id = %s")
            params.append(org_id)

        if start_dt:
            clauses.append("c.start_time >= %s")
            params.append(start_dt)

        if end_dt:
            clauses.append("c.end_time <= %s")
            params.append(end_dt)

        if keyword:
            kw = f"%{keyword.lower()}%"
            clauses.append(
                "(LOWER(emp.emp_name) LIKE %s OR LOWER(auth.username) LIKE %s)"
            )
            params.extend([kw, kw])

        where_sql = " AND ".join(clauses) if clauses else "1=1"

        sql = f"""
            SELECT
                ev.id AS eval_id,
                ev.evaluation_status,
                ev.final_score,
                ev.rule_score,
                ev.attendance_rate,
                ev.leave_rate,
                c.cycle_name,
                c.start_time,
                c.end_time,
                emp.emp_name,
                emp.emp_id,
                org.org_name,
                auth.username
            FROM performance_evaluation ev
            JOIN performance_cycle c ON ev.cycle_id = c.id
            JOIN employee emp ON ev.emp_id = emp.id
            LEFT JOIN organization org ON emp.org_id = org.id
            LEFT JOIN auth_user auth ON emp.user_id = auth.id
            WHERE {where_sql}
            ORDER BY c.start_time DESC, emp.emp_name ASC
            LIMIT {self.max_rows}
        """

        rows: list[dict[str, Any]] = []
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            description = cursor.description or []
            col_names = [col[0] for col in description]
            for db_row in cursor.fetchall():
                rows.append(dict(zip(col_names, db_row)))

        status_map = dict(PerformanceEvaluation.EVAL_STATUS_CHOICES)
        for row in rows:
            eval_status = row.get("evaluation_status")
            status_key = str(eval_status) if eval_status is not None else ""
            row["status_label"] = status_map.get(status_key, eval_status)
            att = row.get("attendance_rate")
            leave = row.get("leave_rate")
            row["attendance_rate_display"] = (
                None if att is None else f"{float(att) * 100:.2f}%"
            )
            row["leave_rate_display"] = (
                None if leave is None else f"{float(leave) * 100:.2f}%"
            )

        ctx["orgs"] = Organization.objects.filter(is_deleted=False).order_by("org_name")
        ctx["results"] = rows
        ctx["result_count"] = len(rows)
        ctx["max_rows"] = self.max_rows
        ctx["filters"] = {
            "org": org_id or "",
            "start": start_str or "",
            "end": end_str or "",
            "keyword": keyword,
        }
        return ctx
