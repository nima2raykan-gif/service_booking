from django.urls import path

from .views import (
    business_detail,
    business_list,
    service_detail,
    booking_date_selection,
    booking_time_selection,
    available_booking_times,
    create_booking,
    owner_notifications,
    owner_dashboard,
    owner_business,
    owner_business_edit,
    owner_services,
    owner_service_create,
    owner_service_edit,
    owner_bookings,
    owner_customers,
    mark_notification_read,
    find_customer_by_phone,
)


urlpatterns = [

    path(
        "",
        business_list,
        name="business_list",
    ),

    path(
        "business/<int:business_id>/",
        business_detail,
        name="business_detail",
    ),

    path(
        "service/<int:service_id>/",
        service_detail,
        name="service_detail",
    ),

    path(
        "service/<int:service_id>/booking/",
        booking_date_selection,
        name="booking_date_selection",
    ),

    path(
        "service/<int:service_id>/booking/date/<str:date_value>/",
        booking_time_selection,
        name="booking_time_selection",
    ),

    path(
        "api/service/<int:service_id>/booking/<str:date_value>/times/",
        available_booking_times,
        name="available_booking_times",
    ),

    path(
        "api/service/<int:service_id>/booking/create/",
        create_booking,
        name="create_booking",
    ),

    path(
        "owner/",
        owner_dashboard,
        name="owner_dashboard",
    ),

    path(
        "owner/bookings/",
        owner_bookings,
        name="owner_bookings",
    ),

    path(
        "owner/notifications/",
        owner_notifications,
        name="owner_notifications",
    ),

    path(
        "owner/business/",
        owner_business,
        name="owner_business",
    ),

    path(
        "owner/business/edit/",
        owner_business_edit,
        name="owner_business_edit",
    ),

    path(
        "owner/services/",
        owner_services,
        name="owner_services",
    ),

    path(
        "owner/services/create/",
        owner_service_create,
        name="owner_service_create",
    ),

    path(
        "owner/services/<int:service_id>/edit/",
        owner_service_edit,
        name="owner_service_edit",
    ),

    path(
        "owner/notifications/<int:notification_id>/read/",
        mark_notification_read,
        name="mark_notification_read",
    ),

    path(
        "api/customer/find/",
        find_customer_by_phone,
        name="find_customer_by_phone",
    ),
    path(
    "owner/customers/",
    owner_customers,
    name="owner_customers",
    ),

]