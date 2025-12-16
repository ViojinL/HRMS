from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView, View, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
import openpyxl
from io import BytesIO

from .models import Employee
from .forms import EmployeeImportForm, EmployeeForm
from apps.organization.models import Organization

# 1. 导入处理 View
class EmployeeImportView(LoginRequiredMixin, FormView):
    template_name = 'employee/import.html'
    form_class = EmployeeImportForm
    success_url = '/employee/'

    def form_valid(self, form):
        file = form.cleaned_data['file']
        try:
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            success_count = 0
            errors = []
            
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not row[0]: continue  # 忽略空行
                try:
                    name, emp_id, id_card, phone, email, org_code, position, hire_date, gender = row[:9]
                except ValueError:
                    errors.append(f"第 {row_idx} 行格式错误：列数不足")
                    continue

                if Employee.objects.filter(emp_id=emp_id).exists():
                    errors.append(f"第 {row_idx} 行错误：工号 {emp_id} 已存在")
                    continue
                
                org = Organization.objects.filter(org_code=org_code).first()
                if not org:
                    errors.append(f"第 {row_idx} 行错误：部门编码 {org_code} 不存在")
                    continue
                
                try:
                    with transaction.atomic():
                        user, _ = User.objects.get_or_create(username=emp_id, defaults={'email': email})
                        user.set_password('123456')
                        user.save()
                        
                        if isinstance(hire_date, str):
                            hire_date = timezone.datetime.strptime(hire_date, '%Y-%m-%d').date()
                        
                        Employee.objects.create(
                            emp_id=str(emp_id),
                            emp_name=name,
                            id_card=str(id_card),
                            phone=str(phone),
                            email=email,
                            org=org,
                            position=position,
                            hire_date=hire_date,
                            gender=gender if gender in ['male', 'female'] else 'male',
                            user=user,
                            employment_type='full_time',
                            emp_status='probation',
                            create_by=self.request.user.username,
                            update_by=self.request.user.username
                        )
                        success_count += 1
                except Exception as e:
                    errors.append(f"第 {row_idx} 行入库失败：{str(e)}")

            if success_count > 0:
                messages.success(self.request, f"成功导入 {success_count} 名员工！")
            if errors:
                messages.warning(self.request, f"部分失败：<br>" + "<br>".join(errors[:5]))
                    
        except Exception as e:
            messages.error(self.request, f"文件解析失败: {str(e)}")
            return self.form_invalid(form)
        return redirect(self.success_url)

# 2. 模板下载 View
class EmployeeTemplateDownloadView(LoginRequiredMixin, View):
    def get(self, request):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "员工导入模板"
        headers = ['姓名', '工号', '身份证号', '手机号', '邮箱', '部门编码', '岗位', '入职日期', '性别(male/female)']
        ws.append(headers)
        ws.append(['张三', 'EMP9001', '110101199001011234', '13800000000', 'zhangsan@test.com', 'HR', '人事专员', '2024-01-01', 'male'])
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=employee_template.xlsx'
        return response

# 3. 创建员工 View
class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employee/form.html'
    success_url = reverse_lazy('employee:list')

    def form_valid(self, form):
        last_emp = Employee.objects.order_by('-create_time').first()
        new_id_suffix = 1001
        if last_emp and last_emp.emp_id.startswith('EMP'):
            try:
                new_id_suffix = int(last_emp.emp_id[3:]) + 1
            except ValueError:
                pass
        emp_id = f"EMP{new_id_suffix}"
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=emp_id, 
                    email=form.cleaned_data.get('email'), 
                    password='password123'
                )
                form.instance.emp_id = emp_id
                form.instance.user = user
                form.instance.create_by = self.request.user.username
                form.instance.update_by = self.request.user.username
                messages.success(self.request, f"员工创建成功，工号：{emp_id}")
                return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"创建失败: {e}")
            return self.form_invalid(form)

# 4. 更新员工 View
class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employee/form.html'
    
    def get_success_url(self):
        return reverse_lazy('employee:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.update_by = self.request.user.username
        messages.success(self.request, "员工信息已更新")
        return super().form_valid(form)

# 5. 列表 View
class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'employee/list.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('org', 'manager_emp')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(emp_name__icontains=search) | 
                Q(emp_id__icontains=search) |
                Q(org__org_name__icontains=search)
            )
        return queryset.order_by('emp_id')

# 6. 详情 View
class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'employee/detail.html'
    context_object_name = 'emp'
