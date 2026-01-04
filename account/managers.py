from django.contrib.auth.base_user import BaseUserManager
from django.db import transaction
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):

    def _create_user(self, *, email=None, phone=None, username=None, password, **extra_fields):
        if not password:
            raise ValueError(_("Password must be provided"))

        if not any([email, phone, username]):
            raise ValueError(
                _("User must have at least one identifier: email, phone, or username")
            )

        if email:
            email = self.normalize_email(email)

        with transaction.atomic():
            user = self.model(
                email=email,
                phone=phone,
                username=username,
                **extra_fields,
            )
            user.set_password(password)
            user.save(using=self._db)

        return user

    def create_user(self, *, email=None, phone=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_verified", False)

        return self._create_user(
            email=email,
            phone=phone,
            username=username,
            password=password,
            **extra_fields,
        )

    def create_superuser(self, *, email=None, phone=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True"))

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True"))

        return self._create_user(
            email=email,
            phone=phone,
            username=username,
            password=password,
            **extra_fields,
        )
