from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View, DetailView
from django.db import transaction, IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.template.defaultfilters import truncatechars
from django.contrib.auth import get_user_model
from .models import LeaveApply, LeaveTimeSegment
from .forms import LeaveApplyForm
from apps.employee.models import Employee
from apps.performance.models import PerformanceEvaluation
from apps.performance.services import refresh_metrics_for_queryset
from apps.core.roles import is_performance_admin
from django.utils import timezone
from decimal import Decimal
from utils.sql_scope import (
    build_org_tree_cte,
    get_user_scope,
    normalize_str,
    parse_iso_datetime_local,
    uniq,
)

# ... (Existing imports: LeaveListView, LeaveApplyView) ...


class LeaveListView(LoginRequiredMixin, ListView):
    model = LeaveApply
    template_name = "leave/list.html"
    context_object_name = "leaves"

    def get_queryset(self):
        if not hasattr(self.request.user, "employee"):
            return LeaveApply.objects.none()
        return LeaveApply.objects.filter(emp=self.request.user.employee).order_by(
            "-create_time"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for leave in context.get("leaves", []):
            leave.leave_type_label = leave.get_leave_type_display()
        return context


class LeaveApplyView(LoginRequiredMixin, View):
    def get(self, request):
        form = LeaveApplyForm()
        return render(request, "leave/apply.html", {"form": form})

    def post(self, request):
        if hasattr(request.user, "employee"):
            employee = request.user.employee
        else:
            messages.error(request, "系统未配置员工档案，无法提交")
            return redirect("leave:list")

        form = LeaveApplyForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    start_time = form.cleaned_data["start_time"]
                    end_time = form.cleaned_data["end_time"]

                    duration = end_time - start_time
                    days = Decimal(duration.total_seconds() / (24 * 3600)).quantize(
                        Decimal("0.01")
                    )

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
                        update_by=request.user.id,
                    )

                messages.success(request, "请假申请已提交")
                return redirect("leave:list")
            except IntegrityError as e:
                if "no_leave_overlap" in str(e) or "exclude_emp_leave_time" in str(e):
                    messages.error(
                        request,
                        "当前时间段内存在“审核中”或“已批准”的记录，请将旧请假标记为完成后再申请",
                    )
                else:
                    messages.error(request, f"数据库错误：{str(e)}")
            except Exception as e:
                messages.error(request, f"系统错误：{str(e)}")

        return render(request, "leave/apply.html", {"form": form})


class LeaveApprovalListView(LoginRequiredMixin, ListView):
    """
    待办审批列表
    逻辑：查找申请人的直属上级是当前用户的所有 审核中(reviewing) 记录
    """

    model = LeaveApply
    template_name = "leave/approval_list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        if not hasattr(self.request.user, "employee"):
            return LeaveApply.objects.none()

        current_emp = self.request.user.employee
        # 查找所有汇报给当前员工的下属
        subordinates = Employee.objects.filter(manager_emp=current_emp)

        # 查找下属的待审批请求
        return (
            LeaveApply.objects.filter(emp__in=subordinates, apply_status="reviewing")
            .select_related("emp")
            .order_by("create_time")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for task in context.get("tasks", []):
            task.leave_type_label = task.get_leave_type_display()
            task.reason_preview = truncatechars(task.reason or "", 20)

        performance_tasks = []
        if is_performance_admin(self.request.user):
            perf_qs = (
                PerformanceEvaluation.objects.filter(evaluation_status="hr_audit")
                .select_related("emp", "cycle")
                .order_by("cycle__start_time", "emp__emp_name")
            )
            refresh_metrics_for_queryset(perf_qs, save=False)
            performance_tasks = list(perf_qs)

        context["performance_tasks"] = performance_tasks
        context["performance_tasks_count"] = len(performance_tasks)
        return context


class LeaveDetailView(LoginRequiredMixin, DetailView):
    model = LeaveApply
    template_name = "leave/detail.html"
    context_object_name = "leave"

    def get_object(self):
        obj = super().get_object()
        # 权限校验：只能看自己的，或者自己是审批人（上级）
        current_user = self.request.user
        if not hasattr(current_user, "employee"):
            raise PermissionDenied

        current_emp = current_user.employee
        is_owner = obj.emp == current_emp
        is_manager = obj.emp.manager_emp == current_emp

        if not (is_owner or is_manager or current_user.is_superuser):
            raise PermissionDenied
        # 保存权限上下文，供模板使用
        self._is_owner = is_owner
        return obj

    def _format_datetime(self, value, fmt="%Y-%m-%d %H:%M"):
        if not value:
            return "--"
        return timezone.localtime(value).strftime(fmt)

    def _build_segment_rows(self, leave):
        rows = []
        for segment in leave.segments.all():
            rows.append(
                {
                    "range_label": f"{self._format_datetime(segment.leave_start_time)} ~ {self._format_datetime(segment.leave_end_time)}",
                    "days_label": f"{segment.segment_days} 天",
                }
            )
        return rows

    def _resolve_approver(self, leave):
        if leave.apply_status == "reviewing":
            return None
        user_model = get_user_model()
        if leave.update_by:
            approver = (
                user_model.objects.filter(pk=leave.update_by)
                .select_related("employee")
                .first()
            )
            if approver:
                employee_profile = getattr(approver, "employee", None)
                if employee_profile:
                    return employee_profile.emp_name
                return approver.get_full_name() or approver.username
        manager_emp = getattr(leave.emp, "manager_emp", None)
        if manager_emp:
            return manager_emp.emp_name
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leave = context.get("leave")
        if leave:
            leave.leave_type_label = leave.get_leave_type_display()
            leave.apply_time_display = self._format_datetime(leave.apply_time)
            leave.update_time_display = self._format_datetime(leave.update_time)
            leave.status_label = leave.get_apply_status_display()
            leave.segment_rows = self._build_segment_rows(leave)
            leave.approver_display = self._resolve_approver(leave)
            leave.can_approve = self._can_approve(leave)
            leave.can_complete = self._can_complete(leave)
            leave.is_owner = getattr(self, "_is_owner", False)
        return context

    def _can_approve(self, leave):
        if leave.apply_status != "reviewing":
            return False
        user = self.request.user
        if user.is_superuser:
            return True
        if not hasattr(user, "employee"):
            return False
        return leave.emp.manager_emp_id == user.employee.pk

    def _can_complete(self, leave: LeaveApply) -> bool:
        if leave.apply_status != "approved":
            return False
        user = self.request.user
        if not hasattr(user, "employee"):
            return False
        return leave.emp_id == user.employee.pk


class LeaveActionView(LoginRequiredMixin, View):
    """
    审批动作：通过/拒绝
    """

    def post(self, request, pk):
        leave = get_object_or_404(LeaveApply, pk=pk)
        action = request.POST.get("action")

        # 权限校验
        if not hasattr(request.user, "employee"):
            messages.error(request, "无权操作")
            return redirect("leave:list")

        current_emp = request.user.employee
        is_owner = leave.emp == current_emp
        is_approver = leave.emp.manager_emp == current_emp or request.user.is_superuser

        if action == "complete":
            if not is_owner:
                messages.error(request, "只能本人完成自己的请假单")
                return redirect("leave:list")
            if leave.apply_status != "approved":
                messages.error(request, "仅已批准的请假单可标记为已完成")
                return redirect("leave:detail", pk=pk)
            leave.apply_status = "completed"
            leave.segments.update(is_active=False)
            messages.success(request, "已将请假单标记为已完成")
        elif action == "approve":
            if not is_approver:
                messages.error(request, "您不是该申请的审批人")
                return redirect("leave:list")
            if leave.apply_status != "reviewing":
                messages.warning(request, "当前状态不可再次审批")
                return redirect("leave:detail", pk=pk)
            leave.apply_status = "approved"
            leave.segments.update(is_active=True)
            messages.success(request, "已批准该申请")
        elif action == "reject":
            if not is_approver:
                messages.error(request, "您不是该申请的审批人")
                return redirect("leave:list")
            if leave.apply_status != "reviewing":
                messages.warning(request, "当前状态不可再次审批")
                return redirect("leave:detail", pk=pk)
            leave.apply_status = "rejected"
            leave.segments.update(is_active=False)
            messages.success(request, "已拒绝该申请")
        else:
            messages.warning(request, "无效的操作")
            return redirect("leave:detail", pk=pk)

        leave.update_by = request.user.id
        leave.save()
        # 跳转：审批人返回待办列表；本人完成后返回列表
        if action == "complete":
            return redirect("leave:list")
        return redirect("leave:approval_list")


class LeaveOrgSqlSearchView(LoginRequiredMixin, View):
    """原生 SQL：上级部门可查询下级部门请假记录，多条件组合；下级不可越权。"""

    template_name = "leave/sql_search.html"
    max_rows = 200

    def get(self, request):
        scope = get_user_scope(
            user_id=request.user.id,
            is_superuser=request.user.is_superuser,
            is_staff=request.user.is_staff,
        )

        if not (scope.is_superuser or scope.is_hr or scope.is_manager):
            raise PermissionDenied

        # Ensure SQL view exists (prevents confusing DB errors)
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('vw_leave_profile')")
            if cursor.fetchone()[0] is None:
                messages.error(
                    request,
                    "缺少数据库视图 vw_leave_profile：请先运行 hrms/apply_views.py 初始化视图。",
                )
                return redirect("core:dashboard")

        root_ids: list[str] = []
        if scope.org_id:
            root_ids.append(scope.org_id)

        if scope.emp_pk:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT org.id
                    FROM organization org
                    WHERE org.is_deleted = FALSE
                      AND org.manager_emp_id = %s
                    """,
                    [scope.emp_pk],
                )
                root_ids.extend([r[0] for r in cursor.fetchall()])

        root_ids = uniq([rid for rid in root_ids if rid])

        # org options
        org_options: list[dict[str, str]] = []
        if scope.is_superuser or scope.is_hr:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, org_name
                    FROM organization
                    WHERE is_deleted = FALSE
                    ORDER BY org_name
                    """
                )
                org_options = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]
        else:
            cte_sql, cte_params = build_org_tree_cte(root_ids)
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    {cte_sql}
                    SELECT o.id, o.org_name
                    FROM organization o
                    WHERE o.is_deleted = FALSE
                      AND o.id IN (SELECT id FROM org_tree)
                    ORDER BY o.org_name
                    """,
                    cte_params,
                )
                org_options = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]

        filter_org = normalize_str(request.GET.get("org"))
        keyword = normalize_str(request.GET.get("keyword"))
        emp_id_exact = normalize_str(request.GET.get("emp_id"))
        leave_type = normalize_str(request.GET.get("leave_type"))
        apply_status = normalize_str(request.GET.get("apply_status"))
        start_dt = parse_iso_datetime_local(request.GET.get("start"))
        end_dt = parse_iso_datetime_local(request.GET.get("end"))
        days_min_raw = normalize_str(request.GET.get("days_min"))
        days_max_raw = normalize_str(request.GET.get("days_max"))

        days_min: Decimal | None = None
        days_max: Decimal | None = None
        try:
            if days_min_raw:
                days_min = Decimal(days_min_raw)
        except Exception:
            days_min = None
        try:
            if days_max_raw:
                days_max = Decimal(days_max_raw)
        except Exception:
            days_max = None

        # Query from view (already filters deleted rows)
        clauses: list[str] = ["1=1"]
        params: list[object] = []

        if not (scope.is_superuser or scope.is_hr):
            cte_sql, cte_params = build_org_tree_cte(root_ids)
            clauses.append("v.org_id IN (SELECT id FROM org_tree)")
            params.extend(cte_params)
        else:
            cte_sql = ""

        if filter_org:
            clauses.append("v.org_id = %s")
            params.append(filter_org)

        if emp_id_exact:
            clauses.append("v.emp_id = %s")
            params.append(emp_id_exact)

        if leave_type:
            clauses.append("v.leave_type = %s")
            params.append(leave_type)

        if apply_status:
            clauses.append("v.apply_status = %s")
            params.append(apply_status)

        # 时间范围基于请假分段的最小/最大区间
        if start_dt:
            clauses.append("v.start_time >= %s")
            params.append(start_dt)

        if end_dt:
            clauses.append("v.end_time <= %s")
            params.append(end_dt)

        if days_min is not None:
            clauses.append("v.total_days >= %s")
            params.append(days_min)

        if days_max is not None:
            clauses.append("v.total_days <= %s")
            params.append(days_max)

        if keyword:
            kw = f"%{keyword.lower()}%"
            clauses.append(
                "(LOWER(v.emp_name) LIKE %s OR LOWER(v.emp_id) LIKE %s OR LOWER(COALESCE(v.reason,'')) LIKE %s)"
            )
            params.extend([kw, kw, kw])

        where_sql = " AND ".join(clauses) if clauses else "1=1"

        sql = f"""
            {cte_sql}
            SELECT
                v.leave_id,
                v.leave_type,
                v.apply_status,
                v.total_days,
                v.apply_time,
                v.emp_id,
                v.emp_name,
                v.org_name,
                v.start_time,
                v.end_time,
                v.reason
            FROM public.vw_leave_profile v
            WHERE {where_sql}
            ORDER BY v.start_time DESC NULLS LAST, v.apply_time DESC
            LIMIT {self.max_rows}
        """

        results: list[dict[str, object]] = []
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            description = cursor.description or []
            col_names = [c[0] for c in description]
            for row in cursor.fetchall():
                results.append(dict(zip(col_names, row)))

        leave_type_map = dict(LeaveApply.LEAVE_TYPE_CHOICES)
        apply_status_map = dict(LeaveApply.STATUS_CHOICES)
        for row in results:
            lt = row.get("leave_type")
            st = row.get("apply_status")
            row["leave_type_label"] = leave_type_map.get(str(lt), lt)
            row["apply_status_label"] = apply_status_map.get(str(st), st)

        ctx = {
            "orgs": org_options,
            "results": results,
            "result_count": len(results),
            "max_rows": self.max_rows,
            "leave_type_choices": LeaveApply.LEAVE_TYPE_CHOICES,
            "apply_status_choices": LeaveApply.STATUS_CHOICES,
            "filters": {
                "org": filter_org,
                "keyword": keyword,
                "emp_id": emp_id_exact,
                "leave_type": leave_type,
                "apply_status": apply_status,
                "start": start_dt or "",
                "end": end_dt or "",
                "days_min": days_min_raw,
                "days_max": days_max_raw,
            },
        }
        return render(request, self.template_name, ctx)
