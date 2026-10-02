from django.contrib import admin

from .models import (
    Business,
    Service,
    Booking,
    BusinessWorkingHour,
    Notification,
)


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = (
    "name",
    "phone",
    "opening_time",
    "closing_time",
    "owner",
    "is_active",
    "created_at",
    )

    search_fields = (
        "name",
        "phone",
        "owner__phone",
    )

    list_filter = (
        "is_active",
        "created_at",
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "business",
        "duration",
        "price",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "business__name",
    )

    list_filter = (
        "is_active",
        "duration",
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "customer_phone",
        "service",
        "start_time",
        "end_time",
        "created_at",
    )

    search_fields = (
        "customer_name",
        "customer_phone",
        "service__name",
    )

    list_filter = (
        "start_time",
        "end_time",
        "created_at",
    )

    ordering = (
        "-start_time",
    )
@admin.register(BusinessWorkingHour)
class BusinessWorkingHourAdmin(admin.ModelAdmin):
    list_display = (
        "business",
        "weekday",
        "is_closed",
        "opening_time",
        "closing_time",
    )

    list_filter = (
        "business",
        "weekday",
        "is_closed",
    )

    ordering = (
        "business",
        "weekday",
    )
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "booking",
        "is_read",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "owner__phone",
        "booking__customer_name",
        "booking__customer_phone",
    )

    list_filter = (
        "is_read",
        "created_at",
    )

    ordering = (
        "-created_at",
    )