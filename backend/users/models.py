import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_("Email Address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False)
    phone_number = PhoneNumberField(_("Phone Number"), blank=False, null=False)

    class UserTypes(models.TextChoices):
        ADMIN = "admin", _("Admin")
        MANAGER = "manager", _("Manager")
        STAFF = "staff", _("Staff")

    type = models.CharField(
        max_length=50, choices=UserTypes.choices, default=UserTypes.STAFF
    )
    is_email_verified = models.BooleanField(
        _("Email Verified"),
        default=False,
        help_text=_("Designates whether this user has verified their email address."),
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]

    objects = CustomUserManager()

    def __str__(self):
        return (
            f"{self.last_name}, {self.first_name} - {self.email} ({self.phone_number})"
        )
