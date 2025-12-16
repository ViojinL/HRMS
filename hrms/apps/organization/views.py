from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import Organization

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or getattr(self.request.user, 'employee', None) and self.request.user.employee.position == 'HR Director'

class OrganizationTreeView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organization/tree.html'
    context_object_name = 'organizations'

    def get_queryset(self):
        # 仅获取顶级节点，后续通过递归模板渲染子节点
        return Organization.objects.filter(
            parent_org__isnull=True, 
            status='active'
        ).prefetch_related('children', 'manager_emp')

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organization/list.html'
    context_object_name = 'orgs'
    paginate_by = 20
    
    def get_queryset(self):
        return Organization.objects.filter(is_deleted=False).order_by('org_code')

class OrganizationCreateView(AdminRequiredMixin, CreateView):
    model = Organization
    fields = ['org_code', 'org_name', 'org_type', 'parent_org', 'manager_emp', 'status', 'effective_time']
    template_name = 'organization/form.html'
    success_url = reverse_lazy('organization:list')

    def form_valid(self, form):
        form.instance.create_by = self.request.user.username
        form.instance.update_by = self.request.user.username
        messages.success(self.request, "组织创建成功")
        return super().form_valid(form)

class OrganizationUpdateView(AdminRequiredMixin, UpdateView):
    model = Organization
    fields = ['org_code', 'org_name', 'org_type', 'parent_org', 'manager_emp', 'status', 'effective_time']
    template_name = 'organization/form.html'
    success_url = reverse_lazy('organization:list')

    def form_valid(self, form):
        form.instance.update_by = self.request.user.username
        messages.success(self.request, "组织信息已更新")
        return super().form_valid(form)

class OrganizationDeleteView(AdminRequiredMixin, DeleteView):
    model = Organization
    success_url = reverse_lazy('organization:list')
    template_name = 'organization/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "组织删除成功")
        return super().delete(request, *args, **kwargs)
