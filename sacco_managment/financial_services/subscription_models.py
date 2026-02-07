from django.db import models
from user_auths.models import User
from account.models import Account
from shortuuid.django_fields import ShortUUIDField
from django.utils import timezone


SUBSCRIPTION_STATUS = (
    ('active', 'Active'),
    ('cancelled', 'Cancelled'),
    ('expired', 'Expired'),
    ('paused', 'Paused'),
)

SUBSCRIPTION_FREQUENCY = (
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('yearly', 'Yearly'),
)


class SubscriptionPlan(models.Model):
    """Defines subscription plans available in the system"""
    plan_id = ShortUUIDField(unique=True, length=10, prefix="PLAN", alphabet="1234567890")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=SUBSCRIPTION_FREQUENCY, default='monthly')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"

    class Meta:
        ordering = ['-created_at']


class Subscription(models.Model):
    """User subscriptions to various plans"""
    subscription_id = ShortUUIDField(unique=True, length=15, prefix="SUB", alphabet="1234567890")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField()
    last_billing_date = models.DateTimeField(null=True, blank=True)
    
    auto_renew = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"

    class Meta:
        ordering = ['-created_at']

    def cancel_subscription(self, reason=None):
        """Cancel the subscription"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.auto_renew = False
        if reason:
            self.cancellation_reason = reason
        self.save()

    def pause_subscription(self):
        """Pause the subscription"""
        self.status = 'paused'
        self.auto_renew = False
        self.save()

    def resume_subscription(self):
        """Resume a paused subscription"""
        if self.status == 'paused':
            self.status = 'active'
            self.auto_renew = True
            self.save()

    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and self.auto_renew


class SubscriptionPayment(models.Model):
    """Track all payments made for subscriptions"""
    payment_id = ShortUUIDField(unique=True, length=15, prefix="SUBPAY", alphabet="1234567890")
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ], default='pending')
    
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    failure_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.payment_id} - {self.subscription.plan.name} - {self.status}"

    class Meta:
        ordering = ['-created_at']
