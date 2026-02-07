from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .subscription_models import Subscription, SubscriptionPlan, SubscriptionPayment
from .subscription_forms import (
    SubscriptionCancellationForm,
    SubscriptionPauseForm,
    SubscriptionCreateForm
)
from account.models import Account
from core.models import Notification
import logging

logger = logging.getLogger(__name__)


@login_required
def subscription_list(request):
    """Display all user subscriptions"""
    subscriptions = Subscription.objects.filter(
        user=request.user
    ).select_related('plan', 'account').order_by('-created_at')
    
    active_subscriptions = subscriptions.filter(status='active')
    cancelled_subscriptions = subscriptions.filter(status='cancelled')
    paused_subscriptions = subscriptions.filter(status='paused')
    
    context = {
        'subscriptions': subscriptions,
        'active_subscriptions': active_subscriptions,
        'cancelled_subscriptions': cancelled_subscriptions,
        'paused_subscriptions': paused_subscriptions,
    }
    return render(request, 'financial_services/subscription_list.html', context)


@login_required
def subscription_detail(request, subscription_id):
    """Display subscription details"""
    subscription = get_object_or_404(
        Subscription,
        subscription_id=subscription_id,
        user=request.user
    )
    
    payments = SubscriptionPayment.objects.filter(
        subscription=subscription
    ).order_by('-created_at')[:10]
    
    context = {
        'subscription': subscription,
        'payments': payments,
    }
    return render(request, 'financial_services/subscription_detail.html', context)


@login_required
def unsubscribe(request, subscription_id):
    """Unsubscribe/Cancel a subscription"""
    subscription = get_object_or_404(
        Subscription,
        subscription_id=subscription_id,
        user=request.user
    )
    
    # Check if already cancelled
    if subscription.status == 'cancelled':
        messages.warning(request, "This subscription is already cancelled.")
        return redirect('financial_services:subscription-detail', subscription_id=subscription_id)
    
    if request.method == 'POST':
        form = SubscriptionCancellationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Build cancellation reason
                    reason_choice = form.cleaned_data['reason']
                    additional_feedback = form.cleaned_data.get('additional_feedback', '')
                    
                    reason_text = dict(form.fields['reason'].choices)[reason_choice]
                    full_reason = f"{reason_text}"
                    if additional_feedback:
                        full_reason += f"\n\nAdditional feedback: {additional_feedback}"
                    
                    # Cancel the subscription
                    subscription.cancel_subscription(reason=full_reason)
                    
                    # Create notification
                    Notification.objects.create(
                        user=request.user,
                        notification_type="None",
                        amount=0,
                        is_read=False
                    )
                    
                    messages.success(
                        request,
                        f"Successfully unsubscribed from {subscription.plan.name}. "
                        f"You will not be charged again."
                    )
                    
                    logger.info(
                        f"User {request.user.username} cancelled subscription "
                        f"{subscription.subscription_id} - Reason: {reason_choice}"
                    )
                    
                    return redirect('financial_services:subscription-list')
                    
            except Exception as e:
                logger.error(f"Subscription cancellation error: {str(e)}")
                messages.error(request, "Failed to cancel subscription. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SubscriptionCancellationForm()
    
    context = {
        'subscription': subscription,
        'form': form,
    }
    return render(request, 'financial_services/unsubscribe.html', context)


@login_required
def pause_subscription(request, subscription_id):
    """Pause a subscription temporarily"""
    subscription = get_object_or_404(
        Subscription,
        subscription_id=subscription_id,
        user=request.user
    )
    
    if subscription.status != 'active':
        messages.warning(request, "Only active subscriptions can be paused.")
        return redirect('financial_services:subscription-detail', subscription_id=subscription_id)
    
    if request.method == 'POST':
        form = SubscriptionPauseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    subscription.pause_subscription()
                    
                    messages.success(
                        request,
                        f"Successfully paused {subscription.plan.name}. "
                        f"You can resume it anytime from your subscriptions page."
                    )
                    
                    logger.info(
                        f"User {request.user.username} paused subscription "
                        f"{subscription.subscription_id}"
                    )
                    
                    return redirect('financial_services:subscription-list')
                    
            except Exception as e:
                logger.error(f"Subscription pause error: {str(e)}")
                messages.error(request, "Failed to pause subscription. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SubscriptionPauseForm()
    
    context = {
        'subscription': subscription,
        'form': form,
    }
    return render(request, 'financial_services/pause_subscription.html', context)


@login_required
def resume_subscription(request, subscription_id):
    """Resume a paused subscription"""
    subscription = get_object_or_404(
        Subscription,
        subscription_id=subscription_id,
        user=request.user
    )
    
    if subscription.status != 'paused':
        messages.warning(request, "Only paused subscriptions can be resumed.")
        return redirect('financial_services:subscription-detail', subscription_id=subscription_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                subscription.resume_subscription()
                
                messages.success(
                    request,
                    f"Successfully resumed {subscription.plan.name}. "
                    f"Your next billing date is {subscription.next_billing_date.strftime('%B %d, %Y')}."
                )
                
                logger.info(
                    f"User {request.user.username} resumed subscription "
                    f"{subscription.subscription_id}"
                )
                
                return redirect('financial_services:subscription-list')
                
        except Exception as e:
            logger.error(f"Subscription resume error: {str(e)}")
            messages.error(request, "Failed to resume subscription. Please try again.")
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'financial_services/resume_subscription.html', context)


@login_required
def available_plans(request):
    """Display available subscription plans"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('amount')
    
    context = {
        'plans': plans,
    }
    return render(request, 'financial_services/available_plans.html', context)


@login_required
@transaction.atomic
def subscribe_to_plan(request, plan_id):
    """Subscribe to a plan"""
    plan = get_object_or_404(SubscriptionPlan, plan_id=plan_id, is_active=True)
    
    # Check if user already has an active subscription to this plan
    existing_subscription = Subscription.objects.filter(
        user=request.user,
        plan=plan,
        status='active'
    ).first()
    
    if existing_subscription:
        messages.warning(request, f"You already have an active subscription to {plan.name}.")
        return redirect('financial_services:subscription-list')
    
    if request.method == 'POST':
        try:
            account = Account.objects.select_for_update().get(user=request.user)
            
            # Check if user has sufficient balance
            if account.account_balance < plan.amount:
                messages.error(request, "Insufficient funds. Please fund your account first.")
                return redirect('financial_services:available-plans')
            
            # Calculate next billing date based on frequency
            next_billing = timezone.now()
            if plan.frequency == 'daily':
                next_billing += timedelta(days=1)
            elif plan.frequency == 'weekly':
                next_billing += timedelta(weeks=1)
            elif plan.frequency == 'monthly':
                next_billing += timedelta(days=30)
            elif plan.frequency == 'quarterly':
                next_billing += timedelta(days=90)
            elif plan.frequency == 'yearly':
                next_billing += timedelta(days=365)
            
            # Create subscription
            subscription = Subscription.objects.create(
                user=request.user,
                account=account,
                plan=plan,
                status='active',
                next_billing_date=next_billing,
                auto_renew=True
            )
            
            # Deduct initial payment
            account.account_balance -= plan.amount
            account.save()
            
            # Create payment record
            SubscriptionPayment.objects.create(
                subscription=subscription,
                user=request.user,
                account=account,
                amount=plan.amount,
                status='completed',
                transaction_reference=f"INITIAL-{subscription.subscription_id}"
            )
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type="Debit Alert",
                amount=int(plan.amount),
                is_read=False
            )
            
            messages.success(
                request,
                f"Successfully subscribed to {plan.name}! "
                f"Your next billing date is {next_billing.strftime('%B %d, %Y')}."
            )
            
            logger.info(
                f"User {request.user.username} subscribed to plan "
                f"{plan.plan_id} - {plan.name}"
            )
            
            return redirect('financial_services:subscription-detail', subscription_id=subscription.subscription_id)
            
        except Account.DoesNotExist:
            messages.error(request, "Account not found. Please contact support.")
            return redirect('financial_services:available-plans')
        except Exception as e:
            logger.error(f"Subscription creation error: {str(e)}")
            messages.error(request, "Failed to create subscription. Please try again.")
            return redirect('financial_services:available-plans')
    
    context = {
        'plan': plan,
    }
    return render(request, 'financial_services/subscribe_confirm.html', context)


@login_required
def subscription_payment_history(request, subscription_id):
    """View payment history for a subscription"""
    subscription = get_object_or_404(
        Subscription,
        subscription_id=subscription_id,
        user=request.user
    )
    
    payments = SubscriptionPayment.objects.filter(
        subscription=subscription
    ).order_by('-created_at')
    
    context = {
        'subscription': subscription,
        'payments': payments,
    }
    return render(request, 'financial_services/subscription_payment_history.html', context)
