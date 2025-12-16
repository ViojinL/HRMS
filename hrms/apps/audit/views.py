from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from .models import AuditLog

class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

class AuditLogListView(SuperUserRequiredMixin, ListView):
    model = AuditLog
    template_name = 'audit/list.html'
    context_object_name = 'logs'
    paginate_by = 20
    ordering = ['-oper_time']

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        module = self.request.GET.get('module')
        
        if search:
            queryset = queryset.filter(
                Q(oper_user__icontains=search) | 
                Q(summary__icontains=search) |
                Q(ip_address__icontains=search)
            )
        
        if module:
            queryset = queryset.filter(table_name=module)
            
        return queryset
