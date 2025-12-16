from django import forms
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

    class Meta:
        model = PerformanceCycle
        fields = ['cycle_name', 'cycle_type', 'start_time', 'end_time', 'org']
        widgets = {
            'cycle_name': forms.TextInput(attrs={'class': 'form-input block w-full'}),
            'cycle_type': forms.Select(attrs={'class': 'form-select block w-full'}),
            'org': forms.Select(attrs={'class': 'form-select block w-full'}),
        }

class SelfEvaluationForm(forms.ModelForm):
    class Meta:
        model = PerformanceEvaluation
        fields = ['self_score'] # 简化版，实际应包含具体指标打分
        widgets = {
             'self_score': forms.NumberInput(attrs={'class': 'form-input block w-full', 'min': 0, 'max': 100}),
        }

class ManagerEvaluationForm(forms.ModelForm):
    class Meta:
        model = PerformanceEvaluation
        fields = ['manager_score', 'final_remark']
        widgets = {
             'manager_score': forms.NumberInput(attrs={'class': 'form-input block w-full', 'min': 0, 'max': 100}),
             'final_remark': forms.Textarea(attrs={'class': 'form-textarea block w-full', 'rows': 3}),
        }
