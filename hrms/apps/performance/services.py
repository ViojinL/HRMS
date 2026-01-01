from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.utils import timezone

from apps.attendance.models import Attendance
from apps.leave.models import LeaveTimeSegment


@dataclass(frozen=True)
class AutoMetrics:
    expected_days: int
    attendance_days: int
    leave_days: Decimal
    attendance_rate: Decimal | None
    leave_rate: Decimal | None


def _to_date(d: datetime | date) -> date:
    return d.date() if isinstance(d, datetime) else d


def count_weekdays(start: date, end: date) -> int:
    if end < start:
        return 0
    cur = start
    total = 0
    while cur <= end:
        if cur.weekday() < 5:
            total += 1
        cur += timedelta(days=1)
    return total


def _overlap_seconds(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> int:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if end <= start:
        return 0
    return int((end - start).total_seconds())


def compute_leave_days(emp, start_dt: datetime, end_dt: datetime) -> Decimal:
    """按请假时间段计算周期内请假天数(支持部分重叠)。"""
    start_dt = timezone.make_aware(start_dt) if timezone.is_naive(start_dt) else start_dt
    end_dt = timezone.make_aware(end_dt) if timezone.is_naive(end_dt) else end_dt

    segments = LeaveTimeSegment.objects.select_related('leave').filter(
        emp=emp,
        leave__apply_status='approved',
        leave_start_time__lt=end_dt,
        leave_end_time__gt=start_dt,
    )

    total = Decimal('0')
    for seg in segments:
        seg_start = seg.leave_start_time
        seg_end = seg.leave_end_time
        full = _overlap_seconds(seg_start, seg_end, seg_start, seg_end)
        if full <= 0:
            continue
        overlap = _overlap_seconds(seg_start, seg_end, start_dt, end_dt)
        if overlap <= 0:
            continue
        ratio = Decimal(overlap) / Decimal(full)
        total += (Decimal(seg.segment_days) * ratio)

    return total


def compute_attendance_days(emp, start_day: date, end_day: date) -> tuple[int, int]:
    """返回(有效出勤天数, 原始考勤记录天数)。

    有效出勤：不含旷工(absent)与请假(leave)。
    """
    qs = Attendance.objects.filter(
        emp=emp,
        attendance_date__gte=start_day,
        attendance_date__lte=end_day,
    )
    total_records = qs.values('attendance_date').distinct().count()

    attended = qs.exclude(attendance_status__in=['absent', 'leave']).values('attendance_date').distinct().count()
    return attended, total_records


def compute_auto_metrics_for_evaluation(evaluation) -> AutoMetrics:
    cycle = evaluation.cycle
    start_dt = cycle.start_time
    end_dt = cycle.end_time

    start_day = _to_date(start_dt)
    end_day = _to_date(end_dt)
    expected = count_weekdays(start_day, end_day)

    leave_days = compute_leave_days(evaluation.emp, start_dt, end_dt)
    attendance_days, total_records = compute_attendance_days(evaluation.emp, start_day, end_day)

    # 若周期内没有任何考勤记录：不强行假设出勤，返回 None 以提示“暂无数据”。
    if total_records == 0 or expected == 0:
        return AutoMetrics(
            expected_days=expected,
            attendance_days=attendance_days,
            leave_days=leave_days,
            attendance_rate=None,
            leave_rate=None,
        )

    attendance_rate = (Decimal(attendance_days) / Decimal(expected)).quantize(Decimal('0.0001'))
    leave_rate = (leave_days / Decimal(expected)).quantize(Decimal('0.0001'))

    # clamp 0..1
    if attendance_rate < 0:
        attendance_rate = Decimal('0')
    if attendance_rate > 1:
        attendance_rate = Decimal('1')
    if leave_rate < 0:
        leave_rate = Decimal('0')
    if leave_rate > 1:
        leave_rate = Decimal('1')

    return AutoMetrics(
        expected_days=expected,
        attendance_days=attendance_days,
        leave_days=leave_days.quantize(Decimal('0.01')),
        attendance_rate=attendance_rate,
        leave_rate=leave_rate,
    )


def refresh_evaluation_metrics(evaluation, *, save: bool = True) -> AutoMetrics:
    metrics = compute_auto_metrics_for_evaluation(evaluation)
    evaluation.attendance_rate = metrics.attendance_rate
    evaluation.leave_rate = metrics.leave_rate
    evaluation.rule_score = evaluation.compute_rule_score() if metrics.attendance_rate is not None else None
    if save:
        evaluation.save(update_fields=['attendance_rate', 'leave_rate', 'rule_score'])
    return metrics


def refresh_metrics_for_queryset(qs, *, save: bool = True):
    # 避免 N+1
    qs = qs.select_related('cycle', 'emp')
    for ev in qs:
        refresh_evaluation_metrics(ev, save=save)
