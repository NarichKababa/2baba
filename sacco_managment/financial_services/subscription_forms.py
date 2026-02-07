from django import forms
from .subscription_models import Subscription, SubscriptionPlan


class SubscriptionCancellationForm(forms.Form):
    """Form for cancelling a subscription"""
    reason = forms.ChoiceField(
        choices=[
            ('too_expensive', 'Too expensive'),
            ('not_using', 'Not using the service'),
            ('found_alternative', 'Found an alternative'),
            ('technical_issues', 'Technical issues'),
            ('other', 'Other'),
        ],
        required=True,
        widget=forms.RadioSelect,
        label="Reason for cancellation"
    )
    
    additional_feedback = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Please provide any additional feedback (optional)'
        }),
        required=False,
        label="Additional Feedback"
    )
    
    confirm_cancellation = forms.BooleanField(
        required=True,
        label="I understand that cancelling will stop all future payments"
    )


class SubscriptionPauseForm(forms.Form):
    """Form for pausing a subscription"""
    pause_duration = forms.ChoiceField(
        choices=[
            ('1_month', '1 Month'),
            ('2_months', '2 Months'),
            ('3_months', '3 Months'),
            ('indefinite', 'Indefinite'),
        ],
        required=True,
        widget=forms.RadioSelect,
        label="Pause Duration"
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Reason for pausing (optional)'
        }),
        required=False,
        label="Reason"
    )


class SubscriptionCreateForm(forms.ModelForm):
    """Form for creating a new subscription"""
    class Meta:
        model = Subscription
        fields = ['plan']
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['plan'].queryset = SubscriptionPlan.objects.filter(is_active=True)
        self.fields['plan'].widget.attrs.update({'class': 'form-control'})
