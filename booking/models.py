from django.db import models


class Business(models.Model):
    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="businesses",
        verbose_name="مالک"
    )

    name = models.CharField(
        max_length=150,
        verbose_name="نام کسب‌وکار"
    )

    image = models.ImageField(
    upload_to="businesses/",
    blank=True,
    null=True,
    verbose_name="تصویر کسب‌وکار"
    )

    phone = models.CharField(
        max_length=20,
        verbose_name="شماره تماس"
    )

    opening_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="ساعت شروع کار"
    )

    closing_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="ساعت پایان کار"
    )

    address = models.TextField(
        blank=True,
        verbose_name="آدرس"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "کسب‌وکار"
        verbose_name_plural = "کسب‌وکارها"

    def __str__(self):
        return self.name


class Service(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="کسب‌وکار"
    )

    name = models.CharField(
        max_length=150,
        verbose_name="نام خدمت"
    )

    duration = models.PositiveIntegerField(
        help_text="مدت زمان به دقیقه",
        verbose_name="مدت زمان"
    )

    price = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        verbose_name="قیمت"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"

    def __str__(self):
        return f"{self.business.name} - {self.name}"


class Booking(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="خدمت"
    )

    customer = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        verbose_name="مشتری"
    )

    customer_name = models.CharField(
        max_length=100,
        verbose_name="نام مشتری"
    )

    customer_phone = models.CharField(
        max_length=20,
        verbose_name="شماره تلفن مشتری"
    )

    start_time = models.DateTimeField(
        verbose_name="زمان شروع"
    )

    end_time = models.DateTimeField(
        verbose_name="زمان پایان"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت رزرو"
    )

    class Meta:
        verbose_name = "رزرو"
        verbose_name_plural = "رزروها"

    def __str__(self):
        return f"{self.customer_name} - {self.service.name}"


class BusinessWorkingHour(models.Model):
    WEEKDAY_CHOICES = [
        (0, "شنبه"),
        (1, "یکشنبه"),
        (2, "دوشنبه"),
        (3, "سه‌شنبه"),
        (4, "چهارشنبه"),
        (5, "پنجشنبه"),
        (6, "جمعه"),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="working_hours",
        verbose_name="کسب‌وکار"
    )

    weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAY_CHOICES,
        verbose_name="روز هفته"
    )

    is_closed = models.BooleanField(
        default=False,
        verbose_name="تعطیل"
    )

    opening_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="ساعت شروع"
    )

    closing_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="ساعت پایان"
    )

    class Meta:
        verbose_name = "ساعت کاری"
        verbose_name_plural = "ساعات کاری"
        ordering = ["weekday"]

    def __str__(self):
        return f"{self.business.name} - {self.get_weekday_display()}"
class Notification(models.Model):
    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="صاحب کسب‌وکار"
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="رزرو"
    )

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان"
    )

    message = models.TextField(
        verbose_name="پیام"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="خوانده شده"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title