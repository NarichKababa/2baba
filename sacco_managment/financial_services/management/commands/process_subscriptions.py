"""
Management command to process subscription renewals
Run this command periodically (e.g., via cron job) to process subscription payments
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from financial_services.subscription_models import Subscription, SubscriptionPayment
from account.models import Account
from core.models import Notification
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process subscription renewals and payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making actual changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no changes will be made'))
        
        now = timezone.now()
        
        # Get all active subscriptions that are due for renewal
        due_subscriptions = Subscription.objects.filter(
            status='active',
            auto_renew=True,
            next_billing_date__lte=now
        ).select_related('user', 'account', 'plan')
        
        self.stdout.write(f'Found {due_subscriptions.count()} subscriptions due for renewal')
        
        successful_renewals = 0
        failed_renewals = 0
        
        for subscription in due_subscriptions:
            try:
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Would process subscription {subscription.subscription_id} '
                        f'for user {subscription.user.username}'
                    )
                    continue
                
                with transaction.atomic():
                    # Lock the account for update
                    account = Account.objects.select_for_update().get(id=subscription.account.id)
                    
                    # Check if user has sufficient balance
                    if account.account_balance < subscription.plan.amount:
                        # Create failed payment record
                        SubscriptionPayment.objects.create(
                            subscription=subscription,
                            user=subscription.user,
                            account=account,
                            amount=subscription.plan.amount,
                            status='failed',
                            failure_reason='Insufficient funds'
                        )
                        
                        # Optionally pause or cancel subscription after multiple failures
                        # For now, just log and continue
                        logger.warning(
                            f'Insufficient funds for subscription {subscription.subscription_id} '
                            f'(User: {subscription.user.username})'
                        )
                        
                        failed_renewals += 1
                        continue
                    
                    # Deduct payment
                    account.account_balance -= subscription.plan.amount
                    account.save()
                    
                    # Create successful payment record
                    payment = SubscriptionPayment.objects.create(
                        subscription=subscription,
                        user=subscription.user,
                        account=account,
                        amount=subscription.plan.amount,
                        status='completed',
                        transaction_reference=f'AUTO-{subscription.subscription_id}-{now.strftime("%Y%m%d%H%M%S")}'
                    )
                    
                    # Update subscription billing dates
                    subscription.last_billing_date = now
                    
                    # Calculate next billing date based on frequency
                    if subscription.plan.frequency == 'daily':
                        subscription.next_billing_date = now + timedelta(days=1)
                    elif subscription.plan.frequency == 'weekly':
                        subscription.next_billing_date = now + timedelta(weeks=1)
                    elif subscription.plan.frequency == 'monthly':
                        subscription.next_billing_date = now + timedelta(days=30)
                    elif subscription.plan.frequency == 'quarterly':
                        subscription.next_billing_date = now + timedelta(days=90)
                    elif subscription.plan.frequency == 'yearly':
                        subscription.next_billing_date = now + timedelta(days=365)
                    
                    subscription.save()
                    
                    # Create notification
                    Notification.objects.create(
                        user=subscription.user,
                        notification_type="Debit Alert",
                        amount=int(subscription.plan.amount),
                        is_read=False
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully renewed subscription {subscription.subscription_id} '
                            f'for user {subscription.user.username} - Payment: {payment.payment_id}'
                        )
                    )
                    
                    successful_renewals += 1
                    
            except Exception as e:
                logger.error(
                    f'Error processing subscription {subscription.subscription_id}: {str(e)}'
                )
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to process subscription {subscription.subscription_id}: {str(e)}'
                    )
                )
                failed_renewals += 1
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Summary ===\n'
                f'Total subscriptions processed: {due_subscriptions.count()}\n'
                f'Successful renewals: {successful_renewals}\n'
                f'Failed renewals: {failed_renewals}'
            )
        )
