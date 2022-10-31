from email.policy import default
from random import choices
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings

import datetime as dt
import uuid
from datetime import datetime, timedelta

today = dt.date.today()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=14, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

'''
Generate a unique phone number and save it to the database and assign it to the user
'''

def generate_phone_number():
    return uuid.uuid4().hex[:14].upper()

def pre_save_create_phone_number(sender, instance, *args, **kwargs):
    if not instance.phone_number:
        instance.phone_number = generate_phone_number()

pre_save.connect(pre_save_create_phone_number, sender=User)

# User Settings

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=None)
    account_verified = models.BooleanField(default=False)
    verified_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_expiry = models.DateTimeField(default=datetime.now() + timedelta(days=settings.VERIFY_EXPIRE_DAYS))
    code_expity = models.BooleanField(default=False)
    recieve_email_notice = models.BooleanField(default=True)

# User Payment History

class UserPaymentHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    paystack_access_code = models.CharField(max_length=100, blank=True, null=True)
    payment_for = models.ForeignKey('Subscription', on_delete=models.SET_NULL, default=None, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email

# User's Subscription Choices

class SubscriptionChoices(models.Model):
    SUBSCRIPTION_CHOICES = (
        ('Globalnet Bronze', 'Globalnet Bronze'),
        ('Globalnet Silver', 'Globalnet Silver'),
        ('Globalnet Gold', 'Globalnet Gold'),
    )
    PERIOD_DURATION = (
        ('Days', 'Days'),
        ('Weeks', 'Weeks'),
        ('Months', 'Months'),
    )
    slug = models.SlugField(null=True, blank=True)
    subscription_type = models.CharField(choices=SUBSCRIPTION_CHOICES, max_length=50, default='Globalnet Bronze')
    duration = models.PositiveIntegerField(default=365)
    duration_period = models.CharField(choices=PERIOD_DURATION, max_length=50, default='Days')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.subscription_type

# User's Subscription
class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_subscription')
    subscription = models.ForeignKey(SubscriptionChoices, on_delete=models.SET_NULL, null=True, related_name='user_subscription')
    reference_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.email

@receiver(post_save, sender=UserSubscription)
def create_subscription(sender, instance, created, **kwargs):
    if instance:
        Subscription.object.create(user_subscription=instance, expires_in=datetime.now().date() + timedelta(days=instance.subscription.duration))

class Subscription(models.Model):
    user_membership = models.ForeignKey(UserSubscription, related_name='_subscription', on_delete=models.CASCADE, default=None)
    expires_in = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
      return self.user_membership.user.username

@receiver(post_save, sender=Subscription)
def update_active(sender, instance, *args, **kwargs):
	if instance.expires_in < today:
		subscription = Subscription.objects.get(id=instance.id)
		subscription.delete()