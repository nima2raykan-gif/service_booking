import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")

        user = self.model(
            phone=phone,
            **extra_fields
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not password:
            raise ValueError("Superuser must have a password")

        return self.create_user(
            phone=phone,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="شناسه"
    )

    phone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="شماره تلفن"
    )

    email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name="ایمیل"
    )

    first_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="نام"
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="نام خانوادگی"
    )

    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name="شماره تلفن تأیید شده"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    is_staff = models.BooleanField(
        default=False,
        verbose_name="دسترسی به پنل مدیریت"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    objects = UserManager()

    USERNAME_FIELD = "phone"

    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.phone