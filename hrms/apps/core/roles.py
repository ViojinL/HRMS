from django.contrib.auth.models import AbstractUser


def _extract_employee(user: AbstractUser):
    return getattr(user, 'employee', None)


def is_performance_admin(user: AbstractUser) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    emp = _extract_employee(user)
    if not emp:
        return False

    position = (emp.position or '').upper()
    org_name_raw = getattr(emp.org, 'org_name', '') or ''
    org_name = org_name_raw.upper()

    return (
        position == 'CFO'
        or '绩效' in (emp.position or '')
        or '绩效' in org_name_raw
        or 'PERFORMANCE' in position
        or 'PERFORMANCE' in org_name
    )
