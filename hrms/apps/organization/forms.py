from django import forms
from .models import Organization

class OrganizationCreateForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['org_name', 'org_type', 'parent_org', 'manager_emp', 'status', 'effective_time']
        widgets = {
            'effective_time': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['org_type'].choices = [choice for choice in self.fields['org_type'].choices if choice[0] != 'company']
        for field in self.fields.values():
            if getattr(field.widget, 'input_type', None) != 'date':
                css = field.widget.attrs.setdefault('class', '')
                field.widget.attrs['class'] = f"{css} w-full border-gray-300 rounded-lg shadow-sm focus:border-primary focus:ring focus:ring-primary/20 transition-colors".strip()

class OrganizationUpdateForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['org_code', 'org_name', 'org_type', 'parent_org', 'manager_emp', 'status', 'effective_time']
        widgets = {
            'effective_time': forms.DateInput(attrs={'type': 'date'}),
            'org_code': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.setdefault('class', '')
            field.widget.attrs['class'] = f"{css} w-full border-gray-300 rounded-lg shadow-sm focus:border-primary focus:ring focus:ring-primary/20 transition-colors".strip()
