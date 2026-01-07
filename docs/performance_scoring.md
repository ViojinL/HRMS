# 绩效得分与出勤/请假率计算规则

## 术语
- 绩效周期：`PerformanceCycle`（月/季/半年/年），包含开始/结束时间和权重：出勤权重 `attendance_weight`、请假权重 `leave_weight`（0-100）。
- 绩效评估：`PerformanceEvaluation`，包含周期、员工、出勤率、请假率、规则得分。

## 规则得分公式
在 `PerformanceEvaluation.compute_rule_score()` 中：
1. 若出勤率或请假率为 `None`，则无法计算，返回 `None`。
2. 权重总和 `total_weight = attendance_weight + leave_weight`，若总和<=0，返回 `None`。
3. 出勤分：`attendance_score = attendance_rate * 100`。
4. 请假分：`leave_score = (1 - leave_rate) * 100`。
5. 规则得分：
   $\text{rule\_score} = \frac{attendance\_score \times attendance\_weight + leave\_score \times leave\_weight}{total\_weight}$
   结果范围 0-100。

## 出勤率/请假率计算
由 `apps.performance.services.compute_auto_metrics_for_evaluation` 计算。

### 1) 统计期与期望工作日
- 取周期 `start_time` 和 `end_time` 的日期部分，计算区间内工作日数（周一至周五）为期望出勤天数 `expected_days`。

### 2) 请假天数 `leave_days`
- 来源：`LeaveTimeSegment`，仅统计 `leave.apply_status = "approved"` 的记录。
- 按时间重叠比例折算：
  - 只计算与周期区间有交集的部分。
  - 按交集秒数占该段总秒数的比例，乘以 `segment_days` 累加。
- 最终保留两位小数。

### 3) 出勤天数 `attendance_days`
- 来源：`Attendance` 记录。
- 统计周期内 distinct `attendance_date` 的记录数，排除状态为 `absent` 或 `leave` 的天数；其他状态（normal/late/early_leave/field/overtime/supplement 等）计为出勤。

### 4) 率的计算
- 若周期内无考勤记录或期望工作日数为 0，则出勤率、请假率均为 `None`（提示“暂无数据”）。
- 否则：
  - 出勤率：`attendance_rate = attendance_days / expected_days`（量纲 0~1，保留 4 位小数，超界会被截断到 0~1）。
  - 请假率：`leave_rate = leave_days / expected_days`（量纲 0~1，保留 4 位小数，超界会被截断到 0~1）。

### 5) 自动回填
- `refresh_evaluation_metrics` 会写回 `attendance_rate`、`leave_rate`，并据此计算 `rule_score`，默认保存到数据库。

## 可调参数/注意点
- 权重：在 `PerformanceCycle` 上配置 `attendance_weight` 与 `leave_weight`（整数百分比）。
- 数据口径：
  - 出勤天数以考勤记录为准，状态为 `absent`、`leave` 不计出勤。
  - 请假天数以已批准的请假段为准，按与周期重叠比例折算。
  - 周末不计入期望工作日。
- 若需要加入节假日或调休规则，可在 `count_weekdays` 或考勤/请假口径上扩展。
