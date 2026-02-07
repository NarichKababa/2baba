from django.contrib import admin
from .models import (
    ExchangeRate,
    Recipient,
    CryptoWallet,
    CryptoTransaction,
    Deposit,
    Withdrawal
)
from .subscription_models import (
    SubscriptionPlan,
    Subscription,
    SubscriptionPayment
)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['base_currency', 'target_currency', 'rate', 'last_updated']
    list_filter = ['base_currency', 'last_updated']
    search_fields = ['base_currency', 'target_currency']


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ['user', 'nickname', 'account_number', 'bank_name', 'created_at']
    list_filter = ['created_at', 'bank_name']
    search_fields = ['user__username', 'nickname', 'account_number']


@admin.register(CryptoWallet)
class CryptoWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'bitcoin_balance', 'ethereum_balance', 'usdt_balance']
    search_fields = ['user__username']


@admin.register(CryptoTransaction)
class CryptoTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'crypto_type', 'amount', 'transaction_type', 'fiat_amount', 'timestamp']
    list_filter = ['crypto_type', 'transaction_type', 'timestamp']
    search_fields = ['transaction_id', 'user__username']


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['deposit_id', 'user', 'amount', 'method', 'status', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['deposit_id', 'user__username']


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['withdrawal_id', 'user', 'amount', 'method', 'status', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['withdrawal_id', 'user__username']


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_id', 'name', 'amount', 'frequency', 'is_active', 'created_at']
    list_filter = ['frequency', 'is_active', 'created_at']
    search_fields = ['plan_id', 'name']
    list_editable = ['is_active']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['subscription_id', 'user', 'plan', 'status', 'next_billing_date', 'auto_renew', 'created_at']
    list_filter = ['status', 'auto_renew', 'created_at', 'plan']
    search_fields = ['subscription_id', 'user__username', 'plan__name']
    readonly_fields = ['subscription_id', 'created_at', 'updated_at', 'cancelled_at']
    
    fieldsets = (
        ('Subscription Information', {
            'fields': ('subscription_id', 'user', 'account', 'plan', 'status')
        }),
        ('Billing Information', {
            'fields': ('start_date', 'end_date', 'next_billing_date', 'last_billing_date', 'auto_renew')
        }),
        ('Cancellation Information', {
            'fields': ('cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'subscription', 'user', 'amount', 'status', 'payment_date']
    list_filter = ['status', 'payment_date']
    search_fields = ['payment_id', 'user__username', 'subscription__subscription_id', 'transaction_reference']
    readonly_fields = ['payment_id', 'created_at']
