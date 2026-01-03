from django.contrib import admin
from .models import LeaveReasonConfig


@admin.register(LeaveReasonConfig)
class LeaveReasonConfigAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "max_days",
        "requires_attachment",
        "status",
        "sort_order",
    )
    list_filter = ("status",)
    search_fields = ("code", "name")
    ordering = ("sort_order", "code")
