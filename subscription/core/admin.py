from django.contrib import admin

from .models import SubscriptionChoices, User, Subscription, UserSubscription

admin.site.register(User)
admin.site.register(UserSubscription)
admin.site.register(SubscriptionChoices)
admin.site.register(Subscription)