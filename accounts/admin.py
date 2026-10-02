from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        "phone",
        "first_name",
        "last_name",
        "is_phone_verified",
        "is_active",
        "is_staff",
        "created_at",
    )

    search_fields = (
        "phone",
        "first_name",
        "last_name",
        "email",
    )

    list_filter = (
        "is_phone_verified",
        "is_active",
        "is_staff",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    fieldsets = (
        (
            "اطلاعات کاربر",
            {
                "fields": (
                    "phone",
                    "password",
                    "first_name",
                    "last_name",
                    "email",
                )
            }
        ),
        (
            "وضعیت حساب",
            {
                "fields": (
                    "is_phone_verified",
                    "is_active",
                    "is_staff",
                )
            }
        ),
        (
            "دسترسی‌ها",
            {
                "fields": (
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            }
        ),
        (
            "اطلاعات سیستمی",
            {
                "fields": (
                    "id",
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            }
        ),
    )

    readonly_fields = (
        "id",
        "last_login",
        "created_at",
        "updated_at",
    )