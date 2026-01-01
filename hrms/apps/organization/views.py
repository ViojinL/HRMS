from dataclasses import dataclass, field
from typing import Iterable, List, Optional
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.text import slugify
from .models import Organization
from .forms import OrganizationCreateForm, OrganizationUpdateForm

ORG_TYPE_DISPLAY = {value: label for value, label in Organization.ORG_TYPE_CHOICES}


@dataclass
class OrganizationNode:
    org: Organization
    children: list = field(default_factory=list)

    @property
    def type_display(self) -> str:
        label = ORG_TYPE_DISPLAY.get(self.org.org_type)
        return label or self.org.org_type.replace('_', ' ').capitalize()

    @property
    def manager_display(self) -> Optional[str]:
        return getattr(self.org.manager_emp, 'emp_name', None)

class AdminRequiredMixin(UserPassesTestMixin):
    request: HttpRequest  # provided by CBV at runtime

    def test_func(self) -> bool:
        emp = getattr(self.request.user, 'employee', None)
        return self.request.user.is_superuser or (emp is not None and emp.position == 'HR Director')

class OrganizationTreeView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organization/tree.html'
    context_object_name = 'root_orgs'

    def get_queryset(self):
        # 仅获取顶级节点，后续通过递归模板渲染子节点
        return Organization.objects.filter(
            parent_org__isnull=True,
            status='enabled',
            is_deleted=False
        ).prefetch_related('manager_emp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_key = self.context_object_name or 'root_orgs'
        root_orgs = context.get(context_key, [])
        context['org_tree'] = self.build_tree(root_orgs)
        return context

    def build_tree(self, organizations: Iterable[Organization]) -> List[OrganizationNode]:
        return [self.build_node(org) for org in organizations]

    def build_node(self, org: Organization) -> OrganizationNode:
        active_children = Organization.objects.filter(
            parent_org=org,
            status='enabled',
            is_deleted=False
        ).order_by('org_code')
        return OrganizationNode(
            org=org,
            children=[self.build_node(child) for child in active_children]
        )

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organization/list.html'
    context_object_name = 'orgs'
    paginate_by = 20
    
    def get_queryset(self):
        return Organization.objects.filter(is_deleted=False).order_by('org_code')

class OrganizationCreateView(AdminRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationCreateForm
    template_name = 'organization/form.html'
    success_url = reverse_lazy('organization:list')

    def _generate_org_code(self, org_name: str) -> str:
        base = slugify(org_name, allow_unicode=False).replace('-', '').upper()
        if not base:
            base = 'ORG'
        base = base[:8]
        candidate = base
        counter = 1
        while Organization.objects.filter(org_code=candidate).exists():
            counter += 1
            candidate = f"{base}-{counter}"
        return candidate

    def form_valid(self, form):
        form.instance.org_code = self._generate_org_code(form.cleaned_data['org_name'])
        form.instance.create_by = self.request.user.username
        form.instance.update_by = self.request.user.username
        messages.success(self.request, "组织创建成功")
        return super().form_valid(form)

class OrganizationUpdateView(AdminRequiredMixin, UpdateView):
    model = Organization
    form_class = OrganizationUpdateForm
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
