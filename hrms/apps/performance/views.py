from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from .models import PerformanceCycle, PerformanceEvaluation
from .forms import PerformanceCycleForm, SelfEvaluationForm, ManagerEvaluationForm
from apps.employee.models import Employee

class PerformanceDashboardView(LoginRequiredMixin, ListView):
    template_name = 'performance/dashboard.html'
    context_object_name = 'cycles'
    
    def get_queryset(self):
        # 展示所有开启的绩效周期
        return PerformanceCycle.objects.filter(status__in=['in_progress', 'not_started']).order_by('-start_time')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'employee'):
            emp = self.request.user.employee
            # 查找我的评估记录
            ctx['my_evaluations'] = PerformanceEvaluation.objects.filter(emp=emp)
            # 查找待我评估的记录（作为经理）
            subordinates = Employee.objects.filter(manager_emp=emp)
            ctx['team_evaluations'] = PerformanceEvaluation.objects.filter(
                emp__in=subordinates, 
                evaluation_status__in=['manager_eval', 'hr_audit']
            )
        return ctx

class PerformanceCycleCreateView(LoginRequiredMixin, CreateView):
    # 仅HR/管理员可用
    model = PerformanceCycle
    form_class = PerformanceCycleForm
    template_name = 'performance/cycle_form.html'
    success_url = reverse_lazy('performance:dashboard')

    def form_valid(self, form):
        form.instance.create_by = self.request.user.id
        form.instance.update_by = self.request.user.id
        messages.success(self.request, "绩效周期创建成功")
        return super().form_valid(form)

class MyEvaluationListView(LoginRequiredMixin, ListView):
    template_name = 'performance/my_list.html'
    context_object_name = 'evaluations'

    def get_queryset(self):
        if not hasattr(self.request.user, 'employee'):
            return []
        return PerformanceEvaluation.objects.filter(emp=self.request.user.employee)

class DoSelfEvaluationView(LoginRequiredMixin, UpdateView):
    model = PerformanceEvaluation
    form_class = SelfEvaluationForm
    template_name = 'performance/do_evaluation.html'
    success_url = reverse_lazy('performance:my_list')

    def form_valid(self, form):
        # 更新状态
        self.object = form.save(commit=False)
        self.object.evaluation_status = 'manager_eval' # 提交后转给上级
        self.object.save()
        messages.success(self.request, "自评已提交")
        return super().form_valid(form)

class TeamEvaluationListView(LoginRequiredMixin, ListView):
    template_name = 'performance/team_list.html'
    context_object_name = 'evaluations'

    def get_queryset(self):
        if not hasattr(self.request.user, 'employee'):
            return []
        emp = self.request.user.employee
        subordinates = Employee.objects.filter(manager_emp=emp)
        return PerformanceEvaluation.objects.filter(emp__in=subordinates)

class DoManagerEvaluationView(LoginRequiredMixin, UpdateView):
    model = PerformanceEvaluation
    form_class = ManagerEvaluationForm
    template_name = 'performance/do_evaluation.html'
    success_url = reverse_lazy('performance:team_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_manager'] = True
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        # 简单逻辑：上级评分后直接完成，或者计算总分
        # 实际逻辑应加权计算: final = self * 0.2 + manager * 0.8
        if self.object.self_score and self.object.manager_score:
            self.object.final_score = (self.object.self_score * 0.2) + (self.object.manager_score * 0.8)
        
        self.object.evaluation_status = 'completed'
        self.object.save()
        messages.success(self.request, "绩效评分已完成")
        return super().form_valid(form)
