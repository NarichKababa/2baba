# Deployment Checklist - Subscription Unsubscribe Feature

## Pre-Deployment Steps

### 1. Database Migrations ⚠️ REQUIRED
```bash
cd /vercel/sandbox/sacco_managment
python3 manage.py makemigrations financial_services
python3 manage.py migrate
```

**Expected Output:**
```
Migrations for 'financial_services':
  financial_services/migrations/0002_subscription_models.py
    - Create model SubscriptionPlan
    - Create model Subscription
    - Create model SubscriptionPayment
```

### 2. Verify Installation
```bash
# Check if models are accessible
python3 manage.py shell -c "from financial_services.subscription_models import SubscriptionPlan, Subscription, SubscriptionPayment; print('✅ Models imported successfully')"
```

### 3. Create Initial Subscription Plans
```bash
python3 manage.py shell
```

```python
from financial_services.subscription_models import SubscriptionPlan

# Create sample plans
plans = [
    {
        'name': 'Basic Monthly',
        'description': 'Basic features with monthly billing',
        'amount': 9.99,
        'frequency': 'monthly'
    },
    {
        'name': 'Premium Monthly',
        'description': 'All features with monthly billing',
        'amount': 29.99,
        'frequency': 'monthly'
    },
    {
        'name': 'Annual Premium',
        'description': 'All features with annual billing (save 20%)',
        'amount': 287.88,
        'frequency': 'yearly'
    }
]

for plan_data in plans:
    SubscriptionPlan.objects.create(**plan_data, is_active=True)
    print(f"✅ Created: {plan_data['name']}")

print(f"\n✅ Total plans created: {SubscriptionPlan.objects.count()}")
exit()
```

### 4. Verify URLs
```bash
python3 manage.py show_urls | grep subscription
```

**Expected URLs:**
- `/financial-services/subscriptions/`
- `/financial-services/subscriptions/<subscription_id>/`
- `/financial-services/subscriptions/<subscription_id>/unsubscribe/`
- `/financial-services/plans/`

### 5. Run Tests (if available)
```bash
python3 manage.py test financial_services
```

## Deployment Steps

### 1. Collect Static Files
```bash
python3 manage.py collectstatic --noinput
```

### 2. Check for Errors
```bash
python3 manage.py check
```

**Expected Output:**
```
System check identified no issues (0 silenced).
```

### 3. Restart Application Server
```bash
# For development
python3 manage.py runserver

# For production (example with gunicorn)
gunicorn sacco_managment.wsgi:application --bind 0.0.0.0:8000
```

## Post-Deployment Verification

### 1. Test User Flow
- [ ] Login as a test user
- [ ] Navigate to `/financial-services/plans/`
- [ ] Verify plans are displayed
- [ ] Subscribe to a plan
- [ ] Verify payment deduction
- [ ] Navigate to `/financial-services/subscriptions/`
- [ ] Verify subscription appears
- [ ] Click on subscription
- [ ] Click "Unsubscribe"
- [ ] Complete cancellation form
- [ ] Verify success message
- [ ] Verify subscription status = "cancelled"
- [ ] Verify no future charges

### 2. Test Admin Interface
- [ ] Login to admin panel
- [ ] Navigate to `/admin/financial_services/subscriptionplan/`
- [ ] Verify plans are visible
- [ ] Navigate to `/admin/financial_services/subscription/`
- [ ] Verify subscriptions are visible
- [ ] Check cancellation reason is saved
- [ ] Navigate to `/admin/financial_services/subscriptionpayment/`
- [ ] Verify payments are recorded

### 3. Test Edge Cases
- [ ] Try to unsubscribe already-cancelled subscription
- [ ] Try to access another user's subscription
- [ ] Try to subscribe with insufficient balance
- [ ] Try to pause and resume subscription
- [ ] Verify payment history displays correctly

## Optional: Set Up Automated Renewals

### 1. Test Manual Processing
```bash
# Dry run first
python3 manage.py process_subscriptions --dry-run

# Actual processing
python3 manage.py process_subscriptions
```

### 2. Set Up Cron Job (Production)
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 2 AM
0 2 * * * cd /vercel/sandbox/sacco_managment && /usr/bin/python3 manage.py process_subscriptions >> /var/log/subscription_renewals.log 2>&1
```

## Monitoring

### 1. Check Logs
```bash
# Application logs
tail -f /var/log/django/application.log

# Subscription renewal logs
tail -f /var/log/subscription_renewals.log
```

### 2. Monitor Metrics
- Active subscriptions count
- Cancellation rate
- Failed payment rate
- Revenue from subscriptions

### 3. Review Cancellation Feedback
```bash
python3 manage.py shell
```

```python
from financial_services.subscription_models import Subscription

# Get recent cancellations
recent_cancellations = Subscription.objects.filter(
    status='cancelled'
).order_by('-cancelled_at')[:10]

for sub in recent_cancellations:
    print(f"\nUser: {sub.user.username}")
    print(f"Plan: {sub.plan.name}")
    print(f"Cancelled: {sub.cancelled_at}")
    print(f"Reason: {sub.cancellation_reason}")
    print("-" * 50)
```

## Rollback Plan (If Needed)

### 1. Revert Database Migration
```bash
python3 manage.py migrate financial_services 0001_initial
```

### 2. Revert Code Changes
```bash
git checkout HEAD -- sacco_managment/financial_services/
```

### 3. Remove Templates
```bash
rm -rf sacco_managment/templates/financial_services/subscription_*.html
rm -rf sacco_managment/templates/financial_services/unsubscribe.html
```

## Troubleshooting

### Issue: Migration Fails
**Solution:**
```bash
# Check for conflicts
python3 manage.py showmigrations financial_services

# If needed, fake the migration
python3 manage.py migrate financial_services --fake
```

### Issue: Templates Not Found
**Solution:**
- Verify `TEMPLATES` setting in `settings.py`
- Check template directory exists
- Ensure template names match view references

### Issue: URLs Not Working
**Solution:**
- Verify `financial_services.urls` is included in main `urls.py`
- Check URL patterns are correct
- Run `python3 manage.py show_urls`

### Issue: Permission Denied
**Solution:**
- Check user is logged in
- Verify user owns the subscription
- Check view decorators are correct

## Success Criteria

✅ All migrations applied successfully
✅ Subscription plans created
✅ URLs accessible
✅ User can subscribe to plans
✅ User can unsubscribe from subscriptions
✅ Cancellation feedback is saved
✅ Admin can view all data
✅ No errors in logs
✅ All tests passing

## Documentation

Refer to:
- `UNSUBSCRIBE_FEATURE.md` - Complete feature documentation
- `SUBSCRIPTION_SETUP.md` - Setup guide
- `QUICK_START.md` - Quick reference
- `IMPLEMENTATION_SUMMARY.md` - Implementation details

## Support Contacts

For issues during deployment:
1. Check Django logs
2. Review error messages
3. Consult documentation
4. Contact development team

---

**Deployment Status**: Ready for Deployment
**Last Updated**: February 7, 2026
**Version**: 1.0
