from django import forms
from .models import Employee
from apps.organization.models import Organization

class EmployeeImportForm(forms.Form):
    file = forms.FileField(
        label='选择Excel文件',
        help_text='请上传.xlsx格式文件，大小不超过5MB',
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'})
    )

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['emp_name', 'gender', 'phone', 'email', 'id_card', 
                 'org', 'position', 'hire_date', 'employment_type', 
                 'emp_status', 'manager_emp']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'org': forms.Select(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm'}),
            'manager_emp': forms.Select(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 统一添加 Tailwind 样式
        for field in self.fields:
            if field not in ['org', 'manager_emp']: # Select 已经特殊处理
                self.fields[field].widget.attrs.update({
                    'class': 'w-full border-gray-300 rounded-lg shadow-sm focus:border-primary focus:ring focus:ring-primary/20 transition-colors'
                })
        
        # 过滤组织，只显示启用的
        self.fields['org'].queryset = Organization.objects.filter(status='active')
