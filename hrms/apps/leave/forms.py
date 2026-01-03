from django import forms
from .models import LeaveApply


class LeaveApplyForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label="开始时间",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-input"}
        ),
    )
    end_time = forms.DateTimeField(
        label="结束时间",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-input"}
        ),
    )

    class Meta:
        model = LeaveApply
        fields = ["leave_type", "reason", "attachment_url"]
        widgets = {
            "leave_type": forms.Select(
                attrs={
                    "class": "form-select block w-full mt-1 border-gray-300 rounded-md shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                }
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-textarea block w-full mt-1 border-gray-300 rounded-md shadow-sm",
                    "rows": 3,
                }
            ),
            "attachment_url": forms.TextInput(
                attrs={"class": "form-input block w-full mt-1"}
            ),
        }

    # leave_type choices come from LeaveApply.LEAVE_TYPE_CHOICES

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")

        if start and end and start >= end:
            raise forms.ValidationError("结束时间必须晚于开始时间")
        return cleaned_data
