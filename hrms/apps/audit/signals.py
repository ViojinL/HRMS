from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import AuditLog

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
        
    AuditLog.objects.create(
        table_name='系统认证',
        oper_type='LOGIN',
        summary=f"用户 {user.username} 登录成功",
        oper_user=user.username,
        ip_address=ip
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    # Logout signal user might be None in some cases if session flushed
    if user:
        AuditLog.objects.create(
            table_name='系统认证',
            oper_type='LOGOUT',
            summary=f"用户 {user.username} 退出登录",
            oper_user=user.username,
            ip_address=request.META.get('REMOTE_ADDR')
        )
