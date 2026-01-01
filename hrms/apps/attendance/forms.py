from typing import Any, Dict
from django import forms

from .models import AttendanceShift


class ShiftTimeValidationMixin:
    def clean(self) -> Dict[str, Any]:
        # Pylance-safe super call: ModelForm defines clean at runtime
        cleaned_data: Dict[str, Any] = super().clean()  # type: ignore[misc]
        check_in_start = cleaned_data.get('check_in_start_time')
        check_in_end = cleaned_data.get('check_in_end_time')
        check_out_start = cleaned_data.get('check_out_start_time')
        check_out_end = cleaned_data.get('check_out_end_time')

        if check_in_start and check_in_end and check_in_start >= check_in_end:
            raise forms.ValidationError('上班打卡开始时间必须早于结束时间。')
        if check_out_start and check_out_end and check_out_start >= check_out_end:
            raise forms.ValidationError('下班打卡开始时间必须早于结束时间。')
        return cleaned_data


def _time_widget():
    return forms.TimeInput(attrs={
        'type': 'time',
        'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary',
        'step': 60,
    }, format='%H:%M')


class AttendanceShiftForm(ShiftTimeValidationMixin, forms.ModelForm):
    class Meta:
        model = AttendanceShift
        fields = (
            'shift_name',
            'check_in_start_time',
            'check_in_end_time',
            'check_out_start_time',
            'check_out_end_time',
            'is_active',
        )
        widgets = {
            'check_in_start_time': _time_widget(),
            'check_in_end_time': _time_widget(),
            'check_out_start_time': _time_widget(),
            'check_out_end_time': _time_widget(),
            'shift_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary'
            }),
        }


class AttendanceShiftSettingsForm(ShiftTimeValidationMixin, forms.ModelForm):
    class Meta:
        model = AttendanceShift
        fields = (
            'shift_name',
            'check_in_start_time',
            'check_in_end_time',
            'check_out_start_time',
            'check_out_end_time',
        )
        widgets = {
            'check_in_start_time': _time_widget(),
            'check_in_end_time': _time_widget(),
            'check_out_start_time': _time_widget(),
            'check_out_end_time': _time_widget(),
            'shift_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary'
            }),
        }
