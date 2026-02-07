from django.urls import path
from financial_services import views
from financial_services import subscription_views


app_name = "financial_services"

urlpatterns = [
    
    # Exchange
    path("exchange-rates/", views.exchange_rates, name="exchange-rates"),
    path("currency-exchange/", views.currency_exchange, name="currency-exchange"),
    
    # Recipients
    path("recipients/", views.recipient_list, name="recipient-list"),
    path("recipients/add/", views.add_recipient, name="add-recipient"),
    path("recipients/<int:pk>/edit/", views.edit_recipient, name="edit-recipient"),
    path("recipients/<int:pk>/delete/", views.delete_recipient, name="delete-recipient"),
    
    # Crypto
    path("crypto-wallet/", views.crypto_wallet, name="crypto-wallet"),
    path("buy-crypto/", views.buy_crypto, name="buy-crypto"),
    path("sell-crypto/", views.sell_crypto, name="sell-crypto"),
    
    # Deposit
    path("deposit/", views.initiate_deposit, name="initiate-deposit"),
    path("deposit/process/", views.process_deposit, name="process-deposit"),
    
    # Withdrawal
    path("withdraw/", views.initiate_withdrawal, name="initiate-withdrawal"),
    path("withdraw/process/", views.process_withdrawal, name="process-withdrawal"),
    
    # Subscriptions
    path("subscriptions/", subscription_views.subscription_list, name="subscription-list"),
    path("subscriptions/<str:subscription_id>/", subscription_views.subscription_detail, name="subscription-detail"),
    path("subscriptions/<str:subscription_id>/unsubscribe/", subscription_views.unsubscribe, name="unsubscribe"),
    path("subscriptions/<str:subscription_id>/pause/", subscription_views.pause_subscription, name="pause-subscription"),
    path("subscriptions/<str:subscription_id>/resume/", subscription_views.resume_subscription, name="resume-subscription"),
    path("subscriptions/<str:subscription_id>/payment-history/", subscription_views.subscription_payment_history, name="subscription-payment-history"),
    path("plans/", subscription_views.available_plans, name="available-plans"),
    path("plans/<str:plan_id>/subscribe/", subscription_views.subscribe_to_plan, name="subscribe-to-plan"),
    
    # path('dashboard/', views.dashboard, name='dashboard'),

]
