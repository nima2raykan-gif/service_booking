import re

import jdatetime

from datetime import date, datetime, timedelta

from django.utils import timezone

from .models import (
    Business,
    Booking,
)


def is_business_open_on_date(
    business,
    target_date
):

    weekday = (
        target_date.weekday() + 2
    ) % 7


    working_hour = (
        business.working_hours
        .filter(
            weekday=weekday
        )
        .first()
    )


    if not working_hour:
        return False


    if working_hour.is_closed:
        return False


    if (
        not working_hour.opening_time
        or not working_hour.closing_time
    ):
        return False


    return True



def to_jalali(
    date_value
):

    jalali_date = (
        jdatetime.date.fromgregorian(
            date=date_value
        )
    )


    month_names = [
        "فروردین",
        "اردیبهشت",
        "خرداد",
        "تیر",
        "مرداد",
        "شهریور",
        "مهر",
        "آبان",
        "آذر",
        "دی",
        "بهمن",
        "اسفند",
    ]


    weekday_names = [
        "شنبه",
        "یکشنبه",
        "دوشنبه",
        "سه‌شنبه",
        "چهارشنبه",
        "پنجشنبه",
        "جمعه",
    ]


    return {
        "year":
            jalali_date.year,

        "month":
            jalali_date.month,

        "month_name":
            month_names[
                jalali_date.month - 1
            ],

        "day":
            jalali_date.day,

        "weekday":
            weekday_names[
                jalali_date.weekday()
            ],
    }



def normalize_phone(
    phone
):

    phone = str(
        phone or ""
    ).strip()


    # جلوگیری از ورودی‌های بسیار بزرگ

    if len(phone) > 50:
        return None


    # تبدیل اعداد فارسی به انگلیسی

    persian_digits = (
        "۰۱۲۳۴۵۶۷۸۹"
    )

    english_digits = (
        "0123456789"
    )


    translation_table = str.maketrans(
        persian_digits,
        english_digits
    )


    phone = phone.translate(
        translation_table
    )


    # حذف فاصله، خط تیره و پرانتز

    phone = (
        phone
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )


    # تبدیل فرمت‌های مختلف ایران به 09...

    if phone.startswith("+98"):

        phone = (
            "0"
            + phone[3:]
        )


    elif phone.startswith("0098"):

        phone = (
            "0"
            + phone[4:]
        )


    # اعتبارسنجی نهایی

    if not re.fullmatch(
        r"09\d{9}",
        phone
    ):

        return None


    return phone



def has_available_time_for_service(
    business,
    service,
    target_date
):

    if not is_business_open_on_date(
        business,
        target_date
    ):

        return False


    weekday = (
        target_date.weekday() + 2
    ) % 7


    working_hour = (
        business.working_hours
        .filter(
            weekday=weekday
        )
        .first()
    )


    if not working_hour:
        return False


    if (
        not working_hour.opening_time
        or not working_hour.closing_time
    ):

        return False


    opening_datetime = (
        timezone.make_aware(
            datetime.combine(
                target_date,
                working_hour.opening_time
            )
        )
    )


    closing_datetime = (
        timezone.make_aware(
            datetime.combine(
                target_date,
                working_hour.closing_time
            )
        )
    )


    service_duration = (
        service.duration
    )


    current_datetime = (
        opening_datetime
    )


    while (
        current_datetime
        + timedelta(
            minutes=service_duration
        )
        <= closing_datetime
    ):

        end_datetime = (
            current_datetime
            + timedelta(
                minutes=service_duration
            )
        )


        has_conflict = (
            Booking.objects.filter(
                service__business=business,
                start_time__lt=end_datetime,
                end_time__gt=current_datetime,
            )
            .exists()
        )


        if not has_conflict:

            return True


        current_datetime += timedelta(
            minutes=15
        )


    return False

def get_booking_dates(
    business,
    service=None,
    start_date=None
):

    if start_date is None:
        start_date = date.today()


    booking_dates = []


    for day_offset in range(7):

        target_date = (
            start_date
            + timedelta(
                days=day_offset
            )
        )


        jalali = to_jalali(
            target_date
        )


        # =========================
        # بررسی باز یا تعطیل بودن روز
        # =========================

        business_is_open = (
            is_business_open_on_date(
                business,
                target_date
            )
        )


        # =========================
        # تعطیل
        # =========================

        if not business_is_open:

            booking_dates.append(
                {
                    "date":
                        target_date,

                    "jalali":
                        jalali,

                    "is_available":
                        False,

                    "status":
                        "closed",
                }
            )

            continue


        # =========================
        # اگر سرویس مشخص نشده
        # =========================

        if service is None:

            booking_dates.append(
                {
                    "date":
                        target_date,

                    "jalali":
                        jalali,

                    "is_available":
                        True,

                    "status":
                        "available",
                }
            )

            continue


        # =========================
        # بررسی ظرفیت سرویس
        # =========================

        service_is_available = (
            has_available_time_for_service(
                business,
                service,
                target_date
            )
        )


        if service_is_available:

            status = "available"

        else:

            status = "full"


        booking_dates.append(
            {
                "date":
                    target_date,

                "jalali":
                    jalali,

                "is_available":
                    service_is_available,

                "status":
                    status,
            }
        )


    return booking_dates