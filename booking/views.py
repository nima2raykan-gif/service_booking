import json
import jdatetime
from datetime import date, datetime, timedelta

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from accounts.models import User

from .models import (
    Business,
    Service,
    Booking,
    BusinessWorkingHour,
    Notification,
)

from .services import (
    get_booking_dates,
    normalize_phone,
    is_business_open_on_date,
)


def business_list(request):
    businesses = Business.objects.filter(
        is_active=True
    ).order_by("name")

    return render(
        request,
        "booking/business_list.html",
        {
            "businesses": businesses,
        }
    )


def business_detail(request, business_id):
    business = get_object_or_404(
        Business,
        id=business_id,
        is_active=True
    )

    services = business.services.filter(
        is_active=True
    ).order_by("name")

    working_hours = business.working_hours.all()

    return render(
        request,
        "booking/business_detail.html",
        {
            "business": business,
            "services": services,
            "working_hours": working_hours,
        }
    )


def service_detail(request, service_id):
    service = get_object_or_404(
        Service,
        id=service_id,
        is_active=True,
        business__is_active=True
    )

    return render(
        request,
        "booking/service_detail.html",
        {
            "service": service,
        }
    )


def booking_date_selection(request, service_id):
    service = get_object_or_404(
        Service,
        id=service_id,
        is_active=True,
        business__is_active=True
    )

    booking_dates = get_booking_dates(
    service.business,
    service=service
    )

    return render(
        request,
        "booking/booking_date_selection.html",
        {
            "service": service,
            "booking_dates": booking_dates,
        }
    )


def booking_time_selection(request, service_id, date_value):
    service = get_object_or_404(
        Service,
        id=service_id,
        is_active=True,
        business__is_active=True
    )

    try:
        selected_date = date.fromisoformat(date_value)

    except ValueError:

        return render(
            request,
            "booking/booking_date_selection.html",
            {
                "service": service,
                "booking_dates": get_booking_dates(
                    service.business
                ),
                "error": "تاریخ انتخاب‌شده معتبر نیست.",
            },
        )

    today = date.today()

    max_date = today + timedelta(days=6)

    if selected_date < today or selected_date > max_date:

        return render(
            request,
            "booking/booking_date_selection.html",
            {
                "service": service,
                "booking_dates": get_booking_dates(
                    service.business
                ),
                "error": "تاریخ انتخاب‌شده خارج از محدوده مجاز است.",
            },
        )

    if not is_business_open_on_date(
        service.business,
        selected_date
    ):

        return render(
            request,
            "booking/booking_date_selection.html",
            {
                "service": service,
                "booking_dates": get_booking_dates(
                    service.business
                ),
                "error": "این روز برای کسب‌وکار تعطیل است.",
            },
        )

    return render(
        request,
        "booking/booking_time_selection.html",
        {
            "service": service,
            "selected_date": selected_date,
        },
    )

def available_booking_times(request, service_id, date_value):

    service = get_object_or_404(
        Service,
        id=service_id,
        is_active=True,
        business__is_active=True
    )

    business = service.business

    # -----------------------------
    # 1. اعتبارسنجی تاریخ
    # -----------------------------

    try:

        selected_date = date.fromisoformat(
            date_value
        )

    except ValueError:

        return JsonResponse(
            {
                "success": False,
                "error": "تاریخ انتخاب‌شده معتبر نیست."
            },
            status=400
        )

    today = timezone.localdate()

    max_date = today + timedelta(days=6)

    if selected_date < today or selected_date > max_date:

        return JsonResponse(
            {
                "success": False,
                "error": "تاریخ انتخاب‌شده خارج از محدوده مجاز است."
            },
            status=400
        )

    # -----------------------------
    # 2. بررسی روز کاری کسب‌وکار
    # -----------------------------

    if not is_business_open_on_date(
        business,
        selected_date
    ):

        return JsonResponse(
            {
                "success": True,
                "date": date_value,
                "times": [],
                "booked_intervals": []
            }
        )

    weekday = (
        selected_date.weekday() + 2
    ) % 7

    working_hour = business.working_hours.filter(
        weekday=weekday
    ).first()

    if not working_hour:

        return JsonResponse(
            {
                "success": True,
                "date": date_value,
                "times": [],
                "booked_intervals": []
            }
        )

    opening_time = working_hour.opening_time

    closing_time = working_hour.closing_time

    # -----------------------------
    # 3. ساخت زمان شروع و پایان کار
    # -----------------------------

    opening_datetime = timezone.make_aware(
        datetime.combine(
            selected_date,
            opening_time
        )
    )

    closing_datetime = timezone.make_aware(
        datetime.combine(
            selected_date,
            closing_time
        )
    )

    # -----------------------------
    # 4. دریافت رزروهای موجود آن روز
    # -----------------------------

    existing_bookings = Booking.objects.filter(
        service__business=business,
        start_time__lt=closing_datetime,
        end_time__gt=opening_datetime,
    ).order_by(
        "start_time"
    )

    # -----------------------------
    # 5. آماده‌سازی بازه‌های رزروشده
    # -----------------------------

    booked_intervals = []

    for booking in existing_bookings:

        booking_start = max(
            booking.start_time,
            opening_datetime
        )

        booking_end = min(
            booking.end_time,
            closing_datetime
        )

        # تبدیل UTC به زمان محلی پروژه
        booking_start_local = timezone.localtime(
            booking_start
        )

        booking_end_local = timezone.localtime(
            booking_end
        )

        booked_intervals.append(
            {
                "start":
                    booking_start_local.strftime("%H:%M"),

                "end":
                    booking_end_local.strftime("%H:%M"),

                "start_datetime":
                    booking_start_local.isoformat(),

                "end_datetime":
                    booking_end_local.isoformat(),
            }
        )

    # -----------------------------
    # 6. ساخت ساعت‌های قابل رزرو
    # -----------------------------

    available_times = []

    current_time = opening_datetime

    service_duration = timedelta(
        minutes=service.duration
    )

    while (
        current_time + service_duration
        <= closing_datetime
    ):

        new_start = current_time

        new_end = (
            current_time
            + service_duration
        )

        has_conflict = existing_bookings.filter(
            start_time__lt=new_end,
            end_time__gt=new_start,
        ).exists()

        if not has_conflict:

            available_times.append(
                {
                    "time":
                        current_time.strftime("%H:%M"),

                    "datetime":
                        current_time.isoformat(),
                }
            )

        current_time += timedelta(
            minutes=15
        )

    # -----------------------------
    # 7. پاسخ API
    # -----------------------------

    return JsonResponse(
        {
            "success": True,

            "date":
                date_value,

            "service": {
                "id":
                    service.id,

                "name":
                    service.name,

                "duration":
                    service.duration,
            },

            "business_hours": {
                "opening":
                    opening_time.strftime("%H:%M"),

                "closing":
                    closing_time.strftime("%H:%M"),
            },

            "times":
                available_times,

            "booked_intervals":
                booked_intervals,
        }
    )


def create_booking(request, service_id):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "روش درخواست نامعتبر است."
            },
            status=405
        )

    service = get_object_or_404(
        Service,
        id=service_id,
        is_active=True,
        business__is_active=True
    )

    try:

        data = json.loads(
            request.body
        )

        customer_name = data.get(
            "customer_name",
            ""
        ).strip()

        customer_phone = normalize_phone(
            data.get(
                "customer_phone",
                ""
            )
        )

        date_value = data.get(
            "date",
            ""
        ).strip()

        time_value = data.get(
            "time",
            ""
        ).strip()

        if not customer_name:

            return JsonResponse(
                {
                    "success": False,
                    "error": "نام مشتری الزامی است."
                },
                status=400
            )

        if not customer_phone:

            return JsonResponse(
                {
                    "success": False,
                    "error": "شماره موبایل معتبر نیست."
                },
                status=400
            )

        if not date_value:

            return JsonResponse(
                {
                    "success": False,
                    "error": "تاریخ الزامی است."
                },
                status=400
            )

        if not time_value:

            return JsonResponse(
                {
                    "success": False,
                    "error": "ساعت الزامی است."
                },
                status=400
            )

        selected_date = date.fromisoformat(
            date_value
        )

        selected_time = datetime.strptime(
            time_value,
            "%H:%M"
        ).time()

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "اطلاعات ارسال‌شده معتبر نیست."
            },
            status=400
        )

    today = timezone.localdate()

    max_date = today + timedelta(days=6)

    if (
        selected_date < today
        or selected_date > max_date
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "تاریخ انتخاب‌شده خارج از محدوده مجاز است."
            },
            status=400
        )

    business = service.business

    if not is_business_open_on_date(
        business,
        selected_date
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "این روز برای کسب‌وکار تعطیل است."
            },
            status=400
        )

    weekday = (
        selected_date.weekday() + 2
    ) % 7

    working_hour = business.working_hours.filter(
        weekday=weekday
    ).first()

    if not working_hour:

        return JsonResponse(
            {
                "success": False,
                "error": "ساعات کاری این روز مشخص نشده است."
            },
            status=400
        )

    if (
        not working_hour.opening_time
        or not working_hour.closing_time
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "ساعات کاری این روز معتبر نیست."
            },
            status=400
        )

    start_datetime = timezone.make_aware(
        datetime.combine(
            selected_date,
            selected_time
        )
    )

    end_datetime = (
        start_datetime
        + timedelta(
            minutes=service.duration
        )
    )

    opening_datetime = timezone.make_aware(
        datetime.combine(
            selected_date,
            working_hour.opening_time
        )
    )

    closing_datetime = timezone.make_aware(
        datetime.combine(
            selected_date,
            working_hour.closing_time
        )
    )

    if start_datetime < opening_datetime:

        return JsonResponse(
            {
                "success": False,
                "error": "ساعت انتخاب‌شده خارج از ساعات کاری است."
            },
            status=400
        )

    if end_datetime > closing_datetime:

        return JsonResponse(
            {
                "success": False,
                "error": "مدت خدمت از پایان ساعات کاری عبور می‌کند."
            },
            status=400
        )

    if selected_time.minute not in [
        0,
        15,
        30,
        45
    ]:

        return JsonResponse(
            {
                "success": False,
                "error": "ساعت باید در بازه‌های ۱۵ دقیقه‌ای باشد."
            },
            status=400
        )

    has_conflict = Booking.objects.filter(
        service__business=business,
        start_time__lt=end_datetime,
        end_time__gt=start_datetime,
    ).exists()

    if has_conflict:

        return JsonResponse(
            {
                "success": False,
                "error": "این ساعت دیگر قابل رزرو نیست."
            },
            status=409
        )

    # =========================
    # پیدا کردن یا ایجاد مشتری
    # =========================

    customer, created = User.objects.get_or_create(
        phone=customer_phone,
        defaults={
            "first_name": customer_name,
            "is_active": True,
            "is_phone_verified": False,
        },
    )

    # =========================
    # مشتری جدید
    # =========================

    if created:

        customer.set_unusable_password()

        customer.save(
            update_fields=[
                "password",
            ]
        )

    # =========================
    # مشتری قبلی
    # =========================

    else:

        if customer.first_name != customer_name:

            customer.first_name = customer_name

            customer.save(
                update_fields=[
                    "first_name",
                ]
            )

    # =========================
    # ایجاد رزرو
    # =========================

    booking = Booking.objects.create(
        service=service,
        customer=customer,
        customer_name=customer.first_name,
        customer_phone=customer.phone,
        start_time=start_datetime,
        end_time=end_datetime,
    )

    # =========================
    # ایجاد اعلان
    # =========================

    Notification.objects.create(
        owner=business.owner,
        booking=booking,
        title="رزرو جدید",
        message=(
            f"رزرو جدید برای خدمت «{service.name}» "
            f"برای مشتری {customer.first_name} "
            f"در ساعت {time_value} ثبت شد."
        ),
    )

    return JsonResponse(
        {
            "success": True,
            "booking": {
                "id": booking.id,
                "customer_name": booking.customer_name,
                "customer_phone": booking.customer_phone,
                "date": date_value,
                "time": time_value,
                "service": service.name,
            }
        },
        status=201
    )

def owner_notifications(request):

    notifications = Notification.objects.filter(
        owner=request.user
    ).select_related(
        "booking",
        "booking__service",
    )

    return render(
        request,
        "booking/owner_notifications.html",
        {
            "notifications": notifications,
        }
    )
def find_customer_by_phone(request):
    if request.method != "GET":
        return JsonResponse(
            {
                "success": False,
                "error": "روش درخواست نامعتبر است."
            },
            status=405
        )

    phone = request.GET.get(
        "phone",
        ""
    ).strip()

    phone = normalize_phone(phone)

    if not phone:
        return JsonResponse(
            {
                "success": False,
                "error": "شماره موبایل معتبر نیست."
            },
            status=400
        )

    customer = User.objects.filter(
        phone=phone
    ).first()

    if not customer:
        return JsonResponse(
            {
                "success": True,
                "exists": False,
            }
        )

    return JsonResponse(
        {
            "success": True,
            "exists": True,
            "customer": {
                "id": str(customer.id),
                "name": customer.first_name,
                "phone": customer.phone,
            }
        }
    )

@login_required
def owner_dashboard(request):

    notifications = Notification.objects.filter(
        owner=request.user
    ).select_related(
        "booking",
        "booking__service",
    ).order_by(
        "-created_at"
    )

    unread_count = notifications.filter(
        is_read=False
    ).count()

    notifications = notifications[:5]

    # =========================
    # Today
    # =========================

    today = timezone.localdate()

    bookings_today = Booking.objects.filter(
        service__business__owner=request.user,
        start_time__date=today,
    ).select_related(
        "customer",
        "service",
        "service__business",
    ).order_by(
        "start_time"
    )

    # =========================
    # This Week
    # Saturday -> Friday
    # =========================

    days_since_saturday = (
        today.weekday() + 2
    ) % 7

    week_start = (
        today
        - timedelta(
            days=days_since_saturday
        )
    )

    week_end = (
        week_start
        + timedelta(days=6)
    )

    weekly_bookings = Booking.objects.filter(
        service__business__owner=request.user,
        start_time__date__gte=week_start,
        start_time__date__lte=week_end,
    ).select_related(
        "customer",
        "service",
        "service__business",
    ).order_by(
        "start_time"
    )

    # =========================
    # Weekly Summary
    # =========================

    weekday_names = {
        0: "دوشنبه",
        1: "سه‌شنبه",
        2: "چهارشنبه",
        3: "پنجشنبه",
        4: "جمعه",
        5: "شنبه",
        6: "یکشنبه",
    }

    jalali_weekdays = [
        "شنبه",
        "یکشنبه",
        "دوشنبه",
        "سه‌شنبه",
        "چهارشنبه",
        "پنجشنبه",
        "جمعه",
    ]

    weekly_summary = []

    for index in range(7):

        current_date = (
            week_start
            + timedelta(days=index)
        )

        day_bookings = [
            booking
            for booking in weekly_bookings
            if booking.start_time.astimezone(
                timezone.get_current_timezone()
            ).date() == current_date
        ]

        jalali_date = jdatetime.date.fromgregorian(
            date=current_date
        )

        weekly_summary.append(
            {
                "date": current_date,

                "jalali_date": (
                    f"{jalali_date.year}/"
                    f"{jalali_date.month:02d}/"
                    f"{jalali_date.day:02d}"
                ),

                "weekday": jalali_weekdays[index],

                "count": len(day_bookings),

                "is_today": (
                    current_date == today
                ),
            }
        )

    weekly_booking_count = len(
        weekly_bookings
    )

    # =========================
    # Jalali data for today's bookings
    # =========================

    bookings_data = []

    for booking in bookings_today:

        start_datetime = booking.start_time.astimezone(
            timezone.get_current_timezone()
        )

        created_datetime = booking.created_at.astimezone(
            timezone.get_current_timezone()
        )

        start_jalali = jdatetime.date.fromgregorian(
            date=start_datetime.date()
        )

        created_jalali = jdatetime.date.fromgregorian(
            date=created_datetime.date()
        )

        bookings_data.append(
            {
                "booking": booking,

                "jalali_date": (
                    f"{start_jalali.year}/"
                    f"{start_jalali.month:02d}/"
                    f"{start_jalali.day:02d}"
                ),

                "jalali_created_at": (
                    f"{created_jalali.year}/"
                    f"{created_jalali.month:02d}/"
                    f"{created_jalali.day:02d} "
                    f"{created_datetime.strftime('%H:%M')}"
                ),
            }
        )

    # =========================
    # Jalali data for notifications
    # =========================

    notifications_data = []

    for notification in notifications:

        booking = notification.booking

        start_datetime = booking.start_time.astimezone(
            timezone.get_current_timezone()
        )

        created_datetime = booking.created_at.astimezone(
            timezone.get_current_timezone()
        )

        start_jalali = jdatetime.date.fromgregorian(
            date=start_datetime.date()
        )

        created_jalali = jdatetime.date.fromgregorian(
            date=created_datetime.date()
        )

        notifications_data.append(
            {
                "notification": notification,

                "jalali_date": (
                    f"{start_jalali.year}/"
                    f"{start_jalali.month:02d}/"
                    f"{start_jalali.day:02d}"
                ),

                "jalali_created_at": (
                    f"{created_jalali.year}/"
                    f"{created_jalali.month:02d}/"
                    f"{created_jalali.day:02d} "
                    f"{created_datetime.strftime('%H:%M')}"
                ),
            }
        )

    return render(
        request,
        "booking/owner_dashboard.html",
        {
            "notifications": notifications_data,
            "unread_count": unread_count,
            "bookings_today": bookings_data,
            "weekly_summary": weekly_summary,
            "weekly_booking_count": weekly_booking_count,
        }
    )

@login_required
def owner_bookings(request):

    business = get_object_or_404(
        Business,
        owner=request.user,
        is_active=True,
    )

    bookings = Booking.objects.filter(
        service__business=business,
    ).select_related(
        "customer",
        "service",
    ).order_by(
        "-start_time"
    )

    # =========================
    # Jalali data
    # =========================

    bookings_data = []

    for booking in bookings:

        start_datetime = booking.start_time.astimezone(
            timezone.get_current_timezone()
        )

        end_datetime = booking.end_time.astimezone(
            timezone.get_current_timezone()
        )

        start_jalali = jdatetime.date.fromgregorian(
            date=start_datetime.date()
        )

        bookings_data.append(
            {
                "booking": booking,

                "jalali_date": (
                    f"{start_jalali.year}/"
                    f"{start_jalali.month:02d}/"
                    f"{start_jalali.day:02d}"
                ),

                "start_time": start_datetime.strftime(
                    "%H:%M"
                ),

                "end_time": end_datetime.strftime(
                    "%H:%M"
                ),
            }
        )

    return render(
        request,
        "booking/owner_bookings.html",
        {
            "business": business,
            "bookings": bookings_data,
        }
    )

@login_required
def owner_business(request):

    business = get_object_or_404(
        Business,
        owner=request.user,
        is_active=True,
    )

    return render(
        request,
        "booking/owner_business.html",
        {
            "business": business,
        }
    )


@login_required
def owner_business_edit(request):

    business = get_object_or_404(
        Business,
        owner=request.user,
        is_active=True,
    )

    working_hours = []

    for weekday, weekday_name in BusinessWorkingHour.WEEKDAY_CHOICES:

        working_hour, created = BusinessWorkingHour.objects.get_or_create(
            business=business,
            weekday=weekday,
            defaults={
                "is_closed": False,
                "opening_time": "09:00",
                "closing_time": "18:00",
            },
        )

        working_hours.append(
            working_hour
        )

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        if not name:

            return render(
                request,
                "booking/owner_business_edit.html",
                {
                    "business": business,
                    "working_hours": working_hours,
                    "error": "نام کسب‌وکار الزامی است.",
                }
            )

        business.name = name

        business.phone = phone

        business.address = address

        business.description = description

        image = request.FILES.get(
            "image"
        )

        if image:
            business.image = image

        business.save()

        for working_hour in working_hours:

            is_closed = request.POST.get(
                f"is_closed_{working_hour.weekday}"
            ) == "on"

            opening_time = request.POST.get(
                f"opening_time_{working_hour.weekday}",
                ""
            )

            closing_time = request.POST.get(
                f"closing_time_{working_hour.weekday}",
                ""
            )

            if is_closed:

                working_hour.is_closed = True

                working_hour.opening_time = None

                working_hour.closing_time = None

            else:

                if not opening_time or not closing_time:

                    return render(
                        request,
                        "booking/owner_business_edit.html",
                        {
                            "business": business,
                            "working_hours": working_hours,
                            "error": (
                                f"ساعت شروع و پایان "
                                f"{working_hour.get_weekday_display()} "
                                f"را وارد کنید."
                            ),
                        }
                    )

                try:

                    opening_time_value = datetime.strptime(
                        opening_time,
                        "%H:%M"
                    ).time()

                    closing_time_value = datetime.strptime(
                        closing_time,
                        "%H:%M"
                    ).time()

                except ValueError:

                    return render(
                        request,
                        "booking/owner_business_edit.html",
                        {
                            "business": business,
                            "working_hours": working_hours,
                            "error": "ساعت واردشده معتبر نیست.",
                        }
                    )

                if opening_time_value >= closing_time_value:

                    return render(
                        request,
                        "booking/owner_business_edit.html",
                        {
                            "business": business,
                            "working_hours": working_hours,
                            "error": (
                                f"ساعت پایان "
                                f"{working_hour.get_weekday_display()} "
                                f"باید بعد از ساعت شروع باشد."
                            ),
                        }
                    )

                working_hour.is_closed = False

                working_hour.opening_time = opening_time_value

                working_hour.closing_time = closing_time_value

            working_hour.save()

        return redirect(
            "owner_business"
        )

    return render(
        request,
        "booking/owner_business_edit.html",
        {
            "business": business,
            "working_hours": working_hours,
        }
    )

@login_required
def owner_services(request):

    business = get_object_or_404(
        Business,
        owner=request.user,
        is_active=True,
    )

    services = business.services.all().order_by(
        "-is_active",
        "name",
    )

    return render(
        request,
        "booking/owner_services.html",
        {
            "business": business,
            "services": services,
        }
    )


@login_required
def owner_service_create(request):

    business = get_object_or_404(
        Business,
        owner=request.user,
        is_active=True,
    )

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        duration = request.POST.get(
            "duration",
            ""
        ).strip()

        price = request.POST.get(
            "price",
            ""
        ).strip()

        is_active = request.POST.get(
            "is_active"
        ) == "on"

        if not name:

            return render(
                request,
                "booking/owner_service_create.html",
                {
                    "business": business,
                    "error": "نام خدمت الزامی است.",
                }
            )

        try:

            duration = int(
                duration
            )

        except (
            TypeError,
            ValueError
        ):

            return render(
                request,
                "booking/owner_service_create.html",
                {
                    "business": business,
                    "error": "مدت زمان باید یک عدد معتبر باشد.",
                }
            )

        if duration <= 0:

            return render(
                request,
                "booking/owner_service_create.html",
                {
                    "business": business,
                    "error": "مدت زمان باید بیشتر از صفر باشد.",
                }
            )

        if price:

            try:

                price = int(
                    price
                )

            except (
                TypeError,
                ValueError
            ):

                return render(
                    request,
                    "booking/owner_service_create.html",
                    {
                        "business": business,
                        "error": "قیمت باید یک عدد معتبر باشد.",
                    }
                )

            if price < 0:

                return render(
                    request,
                    "booking/owner_service_create.html",
                    {
                        "business": business,
                        "error": "قیمت نمی‌تواند منفی باشد.",
                    }
                )

        else:

            price = None

        Service.objects.create(
            business=business,
            name=name,
            duration=duration,
            price=price,
            is_active=is_active,
        )

        return redirect(
            "owner_services"
        )

    return render(
        request,
        "booking/owner_service_create.html",
        {
            "business": business,
        }
    )


@login_required
def owner_service_edit(request, service_id):

    business = get_object_or_404(
        Business,
        owner=request.user,
        is_active=True,
    )

    service = get_object_or_404(
        Service,
        id=service_id,
        business=business,
    )

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        duration = request.POST.get(
            "duration",
            ""
        ).strip()

        price = request.POST.get(
            "price",
            ""
        ).strip()

        is_active = request.POST.get(
            "is_active"
        ) == "on"

        if not name:

            return render(
                request,
                "booking/owner_service_edit.html",
                {
                    "business": business,
                    "service": service,
                    "error": "نام خدمت الزامی است.",
                }
            )

        try:

            duration = int(
                duration
            )

        except (
            TypeError,
            ValueError
        ):

            return render(
                request,
                "booking/owner_service_edit.html",
                {
                    "business": business,
                    "service": service,
                    "error": "مدت زمان باید یک عدد معتبر باشد.",
                }
            )

        if duration <= 0:

            return render(
                request,
                "booking/owner_service_edit.html",
                {
                    "business": business,
                    "service": service,
                    "error": "مدت زمان باید بیشتر از صفر باشد.",
                }
            )

        if price:

            try:

                price = int(
                    price
                )

            except (
                TypeError,
                ValueError
            ):

                return render(
                    request,
                    "booking/owner_service_edit.html",
                    {
                        "business": business,
                        "service": service,
                        "error": "قیمت باید یک عدد معتبر باشد.",
                    }
                )

            if price < 0:

                return render(
                    request,
                    "booking/owner_service_edit.html",
                    {
                        "business": business,
                        "service": service,
                        "error": "قیمت نمی‌تواند منفی باشد.",
                    }
                )

        else:

            price = None

        service.name = name

        service.duration = duration

        service.price = price

        service.is_active = is_active

        service.save()

        return redirect(
            "owner_services"
        )

    return render(
        request,
        "booking/owner_service_edit.html",
        {
            "business": business,
            "service": service,
        }
    )


@login_required
def mark_notification_read(request, notification_id):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "روش درخواست نامعتبر است."
            },
            status=405
        )

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        owner=request.user,
    )

    notification.is_read = True

    notification.save(
        update_fields=[
            "is_read"
        ]
    )

    unread_count = Notification.objects.filter(
        owner=request.user,
        is_read=False
    ).count()

    return JsonResponse(
        {
            "success": True,
            "unread_count": unread_count,
        }
    )

@login_required
def owner_customers(request):

    business = get_object_or_404(
        Business,
        owner=request.user,
        is_active=True,
    )

    bookings = Booking.objects.filter(
        service__business=business,
    ).select_related(
        "customer",
        "service",
    ).order_by(
        "start_time"
    )

    customers_map = {}

    for booking in bookings:

        customer = booking.customer

        if not customer:
            continue

        if customer.id not in customers_map:

            customers_map[customer.id] = {
                "customer": customer,
                "booking_count": 0,
                "services": {},
                "last_booking": None,
            }

        customer_data = customers_map[
            customer.id
        ]

        # =========================
        # Total bookings
        # =========================

        customer_data["booking_count"] += 1

        # =========================
        # Bookings by service
        # =========================

        service_name = booking.service.name

        if service_name not in customer_data["services"]:

            customer_data["services"][
                service_name
            ] = 0

        customer_data["services"][
            service_name
        ] += 1

        # =========================
        # Last booking
        # =========================

        if (
            customer_data["last_booking"] is None
            or booking.start_time
            > customer_data["last_booking"].start_time
        ):

            customer_data["last_booking"] = booking


    # =========================
    # Prepare services
    # for template
    # =========================

    customers = []

    for customer_data in customers_map.values():

        services = []

        for service_name, count in (
            customer_data["services"].items()
        ):

            services.append(
                {
                    "name": service_name,
                    "count": count,
                }
            )

        customer_data["services"] = services

        customers.append(
            customer_data
        )


    # =========================
    # Sort by last booking
    # =========================

    customers.sort(
        key=lambda item: (
            item["last_booking"].start_time
            if item["last_booking"]
            else datetime.min
        ),
        reverse=True,
    )


    return render(
        request,
        "booking/owner_customers.html",
        {
            "business": business,
            "customers": customers,
        }
    )