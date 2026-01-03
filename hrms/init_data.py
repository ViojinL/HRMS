"""HRMS 初始化数据（用于本地/演示环境）。

目标：
- 删除现有数据库中的业务数据（便于重复测试）
- 生成组织架构、用户/员工（含绩效部门账号）
- 生成 2024 年考勤/请假数据，确保可计算出勤率与请假率
- 生成 2024 年上下半年两个绩效周期，并标记为“已完成”，评估记录也为“已完成”

运行方式（二选一）：
- 在 hrms 目录：`python init_data.py`
- 或在项目根目录：`python hrms/init_data.py`
"""

import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))  # ensure hrms/ is importable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

import django

django.setup()

from django.core.management import call_command

from django.contrib.auth.models import User
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.core.models import BaseModel  # noqa: F401 (import ensures model registry)
from apps.attendance.models import Attendance
from apps.employee.models import Employee, EmployeeHistory
from apps.leave.models import LeaveApply, LeaveTimeSegment
from apps.organization.models import Organization
from apps.performance.models import (
    PerformanceCycle,
    PerformanceEvaluation,
)
from apps.performance.services import refresh_evaluation_metrics
import argparse


def check_should_run(force=False):
    """检查是否应该运行初始化"""
    if force:
        return True
    if Organization.objects.exists():
        print("跳过初始化：数据库中已存在组织架构数据。使用 --force 强制重置。")
        return False
    return True


DEFAULT_PASSWORD = "Password123!"
SYSTEM_ACTOR_PK: str | None = None


def reset_database():
    """清空数据库数据。

    说明：这里使用 Django 的 `flush` 来删除所有表数据（包含 auth / session / 业务表）。
    这是测试环境的常见做法，便于重复跑初始化脚本。
    """

    print("=== 0) 重置数据库数据 (flush) ===")
    # 确保 schema 已就绪（新环境第一次运行时避免 flush 失败）
    call_command("migrate", interactive=False, verbosity=0)
    call_command("flush", interactive=False, verbosity=0)


def create_user(
    username: str,
    email: str,
    *,
    password: str = DEFAULT_PASSWORD,
    is_staff: bool = False,
    is_superuser: bool = False,
) -> User:
    user = User.objects.create(
        username=username,
        email=email,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )
    user.set_password(password)
    user.save()
    return user


def set_system_actor(user: User):
    global SYSTEM_ACTOR_PK
    SYSTEM_ACTOR_PK = str(user.pk)


def actor_id() -> str:
    if SYSTEM_ACTOR_PK is None:
        raise RuntimeError("System actor is not set")
    return SYSTEM_ACTOR_PK


def create_org(
    org_code: str, org_name: str, org_type: str, *, parent=None, manager=None
):
    org = Organization.objects.create(
        org_code=org_code,
        org_name=org_name,
        org_type=org_type,
        parent_org=parent,
        manager_emp=manager,
        status="enabled",
        effective_time=timezone.make_aware(datetime(2024, 1, 1)),
        create_by=actor_id(),
        update_by=actor_id(),
    )
    return org


def create_employee(
    *,
    username: str,
    name: str,
    emp_id: str,
    org: Organization,
    position: str,
    manager=None,
    password: str = DEFAULT_PASSWORD,
    employment_type: str = "full_time",
    emp_status: str = "active",
    gender: str = "male",
    is_staff: bool = False,
):
    user = create_user(
        username, f"{username}@hrms.com", password=password, is_staff=is_staff
    )
    emp = Employee.objects.create(
        emp_id=emp_id,
        id_card=f"42010119900101{emp_id[-4:]}",
        emp_name=name,
        gender=gender,
        birth_date=datetime(1990, 1, 1).date(),
        phone=f"1380000{emp_id[-4:]}",
        email=f"{username}@hrms.com",
        hire_date=datetime(2024, 1, 2).date(),
        org=org,
        position=position,
        employment_type=employment_type,
        emp_status=emp_status,
        manager_emp=manager,
        user=user,
        create_by=actor_id(),
        update_by=actor_id(),
    )
    return emp


def seed_organizations_and_employees():
    """构建组织架构 + 员工账号（包含绩效部门与 CFO）。"""

    admin_user = create_user(
        "admin", "admin@hrms.com", is_staff=True, is_superuser=True
    )
    set_system_actor(admin_user)

    print("=== 1) 构建组织与员工/账号 ===")

    # 组织结构
    root = create_org("ROOT", "未来科技集团", "company")
    fin = create_org("FIN", "财务与绩效中心", "department", parent=root)
    perf = create_org("PERF", "绩效管理部", "department", parent=fin)
    hr = create_org("HR", "人力资源部", "department", parent=root)
    tech = create_org("TECH", "技术研发中心", "department", parent=root)
    sales = create_org("SALES", "销售与市场部", "department", parent=root)

    fe = create_org("FE", "前端开发组", "team", parent=tech)
    be = create_org("BE", "后端开发组", "team", parent=tech)
    qa = create_org("QA", "质量保障组", "team", parent=tech)
    s_north = create_org("SALES-N", "北区销售组", "team", parent=sales)

    # 用户/员工（密码统一 DEFAULT_PASSWORD）

    ceo = create_employee(
        username="ceo",
        name="张总",
        emp_id="E001",
        org=root,
        position="CEO",
        is_staff=True,
    )
    cfo = create_employee(
        username="cfo",
        name="林财务",
        emp_id="E002",
        org=fin,
        position="CFO",
        manager=ceo,
        is_staff=True,
    )
    perf_admin = create_employee(
        username="perf_admin",
        name="周绩效",
        emp_id="E003",
        org=perf,
        position="绩效经理",
        manager=cfo,
        is_staff=True,
    )
    perf_staff = create_employee(
        username="perf_staff",
        name="孙绩效",
        emp_id="E015",
        org=perf,
        position="绩效专员",
        manager=perf_admin,
    )

    hr_dir = create_employee(
        username="hr_dir",
        name="李人资",
        emp_id="E004",
        org=hr,
        position="HR Director",
        manager=ceo,
        is_staff=True,
    )
    tech_dir = create_employee(
        username="tech_dir",
        name="王技术",
        emp_id="E005",
        org=tech,
        position="Tech Director",
        manager=ceo,
        is_staff=True,
    )
    sales_dir = create_employee(
        username="sales_dir",
        name="刘销售",
        emp_id="E006",
        org=sales,
        position="Sales Director",
        manager=ceo,
        is_staff=True,
    )

    fe_lead = create_employee(
        username="fe_lead",
        name="赵前端",
        emp_id="E007",
        org=fe,
        position="前端组长",
        manager=tech_dir,
    )
    be_lead = create_employee(
        username="be_lead",
        name="孙后端",
        emp_id="E008",
        org=be,
        position="后端组长",
        manager=tech_dir,
    )
    qa_lead = create_employee(
        username="qa_lead",
        name="钱测试",
        emp_id="E009",
        org=qa,
        position="测试组长",
        manager=tech_dir,
    )
    sales_mgr = create_employee(
        username="sales_mgr",
        name="周销售",
        emp_id="E010",
        org=s_north,
        position="销售经理",
        manager=sales_dir,
    )

    dev1 = create_employee(
        username="dev001",
        name="林前端",
        emp_id="E011",
        org=fe,
        position="高级前端",
        manager=fe_lead,
    )
    dev2 = create_employee(
        username="dev002",
        name="陈后端",
        emp_id="E012",
        org=be,
        position="高级后端",
        manager=be_lead,
    )
    qa1 = create_employee(
        username="qa001",
        name="郑测试",
        emp_id="E013",
        org=qa,
        position="测试工程师",
        manager=qa_lead,
    )
    sales1 = create_employee(
        username="sales001",
        name="马销售",
        emp_id="E014",
        org=s_north,
        position="客户经理",
        manager=sales_mgr,
    )

    # 回填负责人（用于 is_manager、组织树展示）
    manager_updates = [
        (root, ceo),
        (fin, cfo),
        (perf, perf_admin),
        (hr, hr_dir),
        (tech, tech_dir),
        (sales, sales_dir),
        (fe, fe_lead),
        (be, be_lead),
        (qa, qa_lead),
        (s_north, sales_mgr),
    ]
    for org, manager in manager_updates:
        Organization.objects.filter(pk=org.pk).update(manager_emp=manager)

    employees = [
        ceo,
        cfo,
        perf_admin,
        perf_staff,
        hr_dir,
        tech_dir,
        sales_dir,
        fe_lead,
        be_lead,
        qa_lead,
        sales_mgr,
        dev1,
        dev2,
        qa1,
        sales1,
    ]

    return {
        "orgs": {
            "root": root,
            "fin": fin,
            "perf": perf,
            "hr": hr,
            "tech": tech,
            "sales": sales,
        },
        "employees": employees,
        "people": {
            "ceo": ceo,
            "cfo": cfo,
            "perf_admin": perf_admin,
            "hr_dir": hr_dir,
            "tech_dir": tech_dir,
            "sales_dir": sales_dir,
            "fe_lead": fe_lead,
            "be_lead": be_lead,
            "qa_lead": qa_lead,
            "sales_mgr": sales_mgr,
            "dev1": dev1,
            "dev2": dev2,
            "qa1": qa1,
            "sales1": sales1,
            "perf_staff": perf_staff,
        },
    }


def _dt(y: int, m: int, d: int, hh: int = 0, mm: int = 0, ss: int = 0) -> datetime:
    return datetime(y, m, d, hh, mm, ss)


def seed_performance_2024_h1_h2(employees):
    """创建 2024 上/下半年两个已完成周期，并写入已完成评估与指标。"""

    print("=== 4) 构建 2024 上/下半年绩效（已完成） ===")

    cycles = [
        {
            "cycle_name": "2024 上半年（H1）全员绩效",
            "cycle_type": "semiannual",
            "start": timezone.make_aware(_dt(2024, 1, 1, 0, 0, 0)),
            "end": timezone.make_aware(_dt(2024, 6, 30, 23, 59, 59)),
        },
        {
            "cycle_name": "2024 下半年（H2）全员绩效",
            "cycle_type": "semiannual",
            "start": timezone.make_aware(_dt(2024, 7, 1, 0, 0, 0)),
            "end": timezone.make_aware(_dt(2024, 12, 31, 23, 59, 59)),
        },
    ]

    created_evals = 0
    for c in cycles:
        cycle = PerformanceCycle.objects.create(
            cycle_name=c["cycle_name"],
            cycle_type=c["cycle_type"],
            start_time=c["start"],
            end_time=c["end"],
            status="archived",
            org=None,
            attendance_weight=60,
            leave_weight=40,
            create_by=actor_id(),
            update_by=actor_id(),
        )

        for emp in employees:
            ev = PerformanceEvaluation.objects.create(
                cycle=cycle,
                emp=emp,
                evaluation_status="completed",
                appeal_status="none",
                final_score=None,
                final_remark="Review completed based on year-to-date metrics.",
                create_by=actor_id(),
                update_by=actor_id(),
            )
            # 让系统基于考勤数据（seed_leave_2024生成的）自动计算规则得分
            refresh_evaluation_metrics(ev, save=True)

            # 最终得分逻辑：在规则得分基础上，进行随机小幅修正（反映人工审核结果）
            if ev.rule_score is not None:
                import random
                # 随机权重：允许最终得分比规则得分高一点或低一点 (-3 到 +2 分)
                adjustment = Decimal(str(round(random.uniform(-3.0, 2.0), 2)))
                ev.final_score = max(Decimal("0"), min(Decimal("100"), ev.rule_score + adjustment))
                ev.save(update_fields=["final_score"])
            else:
                # 兜底分数
                ev.final_score = Decimal("95.00")
                ev.save(update_fields=["final_score"])

    print(f"    Created 2 cycles, {created_evals} evaluations with realistic metrics.")


def seed_leave_2024(people: dict):
    """生成覆盖 2024 上/下半年的批准请假段，确保出勤率产生真实的层次感。"""

    print("=== 2) 构建 2024 请假示例 (approved) ===")

    # 我们通过请假天数来控制“规则得分”：
    # 一个半年周期约 125 个工作日
    # 请 10 天假 -> 约 92 分
    # 请 30 天假 -> 约 76 分
    # 请 60 天假 -> 约 52 分
    # 请 80 天假 -> 约 36 分

    cases = [
        # 极高分组
        (people.get("dev1"), "annual", "Vacation", _dt(2024, 2, 1, 9), _dt(2024, 2, 2, 18), Decimal("2.0")),
        
        # 中等分组 (70-80)
        (people.get("sales_mgr"), "personal", "Personal affairs", _dt(2024, 3, 1, 9), _dt(2024, 4, 1, 18), Decimal("22.0")),
        (people.get("dev2"), "sick", "Medical leave", _dt(2024, 5, 10, 9), _dt(2024, 5, 30, 18), Decimal("15.0")),
        
        # 低分组 (40-60)
        (people.get("qa1"), "personal", "Long leave", _dt(2024, 1, 10, 9), _dt(2024, 3, 30, 18), Decimal("58.0")),
        (people.get("sales1"), "personal", "Family reasons", _dt(2024, 7, 10, 9), _dt(2024, 9, 20, 18), Decimal("52.0")),
        
        # 极低分组 (<40)
        (people.get("be_lead"), "personal", "Major issues", _dt(2024, 1, 5, 9), _dt(2024, 5, 15, 18), Decimal("90.0")),
    ]

    created = 0
    for emp, leave_type, reason, start_dt, end_dt, days in cases:
        if not emp:
            continue
        leave = LeaveApply.objects.create(
            emp=emp,
            leave_type=leave_type,
            apply_status="approved",
            apply_time=timezone.make_aware(start_dt) - timedelta(days=2),
            reason=reason,
            attachment_url=None,
            total_days=days,
            create_by=actor_id(),
            update_by=actor_id(),
        )
        LeaveTimeSegment.objects.create(
            leave=leave,
            emp=emp,
            leave_start_time=timezone.make_aware(start_dt),
            leave_end_time=timezone.make_aware(end_dt),
            segment_days=days,
            create_by=actor_id(),
            update_by=actor_id(),
        )
        created += 1

    print(f"    已创建批准请假段 {created} 条")


def seed_attendance_2024(employees):
    """生成 2024 全年工作日考勤。

    规则：
    - 工作日（周一~周五）生成考勤
    - 若当天在批准请假段内，则标记 attendance_status='leave'
    """

    print("=== 3) 构建 2024 考勤示例（工作日） ===")

    start_day = date(2024, 1, 1)
    end_day = date(2024, 12, 31)

    segments = list(
        LeaveTimeSegment.objects.select_related("leave").filter(
            leave__apply_status="approved",
            leave_start_time__date__lte=end_day,
            leave_end_time__date__gte=start_day,
        )
    )

    leave_days_by_emp: dict[str, set[date]] = {}
    for seg in segments:
        cur = seg.leave_start_time.date()
        last = seg.leave_end_time.date()
        while cur <= last:
            emp_key = getattr(seg, "emp_id")
            leave_days_by_emp.setdefault(emp_key, set()).add(cur)
            cur += timedelta(days=1)

    created = 0
    day = start_day
    while day <= end_day:
        if day.weekday() >= 5:
            day += timedelta(days=1)
            continue

        for emp in employees:
            status = (
                "leave" if day in leave_days_by_emp.get(emp.id, set()) else "normal"
            )
            Attendance.objects.create(
                emp=emp,
                attendance_date=day,
                attendance_type="check_in",
                check_in_time=timezone.make_aware(
                    datetime(day.year, day.month, day.day, 9, 0)
                ),
                check_out_time=timezone.make_aware(
                    datetime(day.year, day.month, day.day, 18, 0)
                ),
                attendance_status=status,
                exception_reason=None,
                appeal_status="none",
                create_by=actor_id(),
                update_by=actor_id(),
            )
            created += 1

        day += timedelta(days=1)

    print(f"    已创建考勤记录 {created} 条")


def main():
    parser = argparse.ArgumentParser(description="HRMS 数据初始化工具")
    parser.add_argument(
        "--force", action="store_true", help="强制执行（会先清空数据库）"
    )
    args = parser.parse_args()

    if not check_should_run(args.force):
        return

    if args.force:
        reset_database()

    ctx = seed_organizations_and_employees()
    employees = ctx["employees"]

    # 先请假 → 再考勤（考勤会把请假日期标记为 leave）
    seed_leave_2024(ctx["people"])
    seed_attendance_2024(employees)

    # 再生成绩效（会刷新并写回出勤/请假率与规则得分）
    seed_performance_2024_h1_h2(employees)

    print("\n初始化完成。")


if __name__ == "__main__":
    main()
