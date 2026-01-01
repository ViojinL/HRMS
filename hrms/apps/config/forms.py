from django import forms
from .models import LeaveReasonConfig


class LeaveReasonConfigForm(forms.ModelForm):
    class Meta:
        model = LeaveReasonConfig
        fields = ['name', 'description', 'max_days', 'requires_attachment', 'status', 'sort_order']
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': '如 annual', 'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'placeholder': '如 年假'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': '简短说明该理由的使用场景'}),
            'max_days': forms.NumberInput(attrs={'step': 0.5, 'min': 0}),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_class = 'w-full rounded-lg border border-gray-200 bg-gray-50 px-4 py-2 text-sm text-gray-700'
        for name, field in self.fields.items():
            if name == 'requires_attachment':
                field.widget.attrs.update({'class': 'h-4 w-4 text-primary focus:ring-primary'})
                continue
            if name == 'status':
                field.widget.attrs.update({'class': 'w-full rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm text-gray-700'})
                continue
            field.widget.attrs.update({'class': base_class})
