import json
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 仅记录已登录用户的部分写操作请求，忽略GET以减少噪音
        if not request.user.is_authenticated:
            return None
            
        if request.method in ['POST', 'PUT', 'DELETE']:
            self._log_action(request)
            
    def _log_action(self, request):
        path = request.path
        if '/admin/' in path or '/static/' in path: # 忽略 Admin 和 Static
            return

        # 尝试解析模块名
        module = 'UNKNOWN'
        if '/leave/' in path: module = '请假管理'
        elif '/performance/' in path: module = '绩效管理'
        elif '/attendance/' in path: module = '考勤管理'
        elif '/employee/' in path: module = '员工管理'
        elif '/organization/' in path: module = '组织管理'
        
        # 尝试解析操作类型
        action = 'ACCESS'
        if request.method == 'POST': action = 'UPDATE/INSERT'
        if request.method == 'DELETE': action = 'DELETE'
        
        # 获取IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # 记录日志
        AuditLog.objects.create(
            table_name=module,
            record_id=path,
            oper_type=action,
            summary=f"用户 {request.user.username} 提交了请求",
            oper_user=request.user.username,
            ip_address=ip,
            # new_data 可以尝试存 request.POST，但要注意脱敏密码
        )
