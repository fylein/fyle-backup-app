from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserProfileManager(BaseUserManager):
    """
    Manager for custom user model
    """

    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        now = timezone.now()
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            is_staff=is_staff,
            is_active=True,
            is_superuser=is_superuser,
            last_login=now,
            date_joined=now,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        user = self._create_user(email, password, True, True, **extra_fields)
        user.save(using=self._db)
        return user


class UserProfile(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model
    """

    email = models.EmailField(max_length=255, unique=True, help_text="Email id of the user")
    name = models.CharField(max_length=255, help_text="Name of the user")
    is_active = models.BooleanField(default=True, help_text="Active user")
    is_superuser = models.BooleanField(default=False, help_text="Super user")
    is_staff = models.BooleanField(default=False, help_text="Staff user")
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    refresh_token = models.CharField(null=True, max_length=512,
                                     help_text='Fyle refresh token of current active account')
    fyle_org_id = models.CharField(max_length=255, null=True,
                                   help_text='Fyle org id of current active account')

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserProfileManager()

    def __str__(self):
        return self.email
