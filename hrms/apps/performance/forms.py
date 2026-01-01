from django import forms
from apps.organization.models import Organization
from .models import PerformanceCycle, PerformanceEvaluation

class PerformanceCycleForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label="开始时间",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'})
    )
    end_time = forms.DateTimeField(
        label="结束时间",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'})
    )

    org = forms.ModelChoiceField(
        queryset=Organization.objects.order_by('org_name'),
        required=False,
        empty_label="全公司",
        label="适用组织",
        help_text='选择"全公司"即可覆盖全公司，或挑选特定部门限定范围。',
        widget=forms.Select(attrs={'class': 'form-select block w-full'}),
    )

    class Meta:
        model = PerformanceCycle
        fields = ['cycle_name', 'cycle_type', 'start_time', 'end_time', 'org', 'attendance_weight', 'leave_weight']
        widgets = {
            'cycle_name': forms.TextInput(attrs={'class': 'form-input block w-full'}),
            'cycle_type': forms.Select(attrs={'class': 'form-select block w-full'}),
            'attendance_weight': forms.NumberInput(attrs={'class': 'form-input block w-full', 'min': 0, 'max': 100}),
            'leave_weight': forms.NumberInput(attrs={'class': 'form-input block w-full', 'min': 0, 'max': 100}),
        }

    def clean(self):
        cleaned = super().clean()
        attendance_weight = cleaned.get('attendance_weight')
        leave_weight = cleaned.get('leave_weight')
        if attendance_weight is None or leave_weight is None:
            return cleaned
        total = attendance_weight + leave_weight
        if total != 100:
            raise forms.ValidationError("规则权重需要相加等于 100%（出勤率占比 + 请假率占比）")
        return cleaned


class PerformanceAdminEvaluationForm(forms.ModelForm):
    """绩效部门统一管理评估：评分/状态/评价。"""

    class Meta:
        model = PerformanceEvaluation
        fields = ['final_score', 'final_remark', 'evaluation_status', 'appeal_status']
        widgets = {
            'final_score': forms.NumberInput(attrs={'class': 'form-input block w-full', 'min': 0, 'max': 100}),
            'final_remark': forms.Textarea(attrs={'class': 'form-textarea block w-full', 'rows': 3}),
            'evaluation_status': forms.Select(attrs={'class': 'form-select block w-full'}),
            'appeal_status': forms.Select(attrs={'class': 'form-select block w-full'}),
        }
