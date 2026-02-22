from django import forms
from django.utils.translation import gettext_lazy as _

from .models import PaymentGatewaySettings, PaymentLink


class PaymentGatewaySettingsForm(forms.ModelForm):
    """Form for payment gateway settings."""

    class Meta:
        model = PaymentGatewaySettings
        fields = [
            'active_gateway',
            'stripe_public_key', 'stripe_secret_key', 'stripe_webhook_secret',
            'redsys_merchant_code', 'redsys_secret_key', 'redsys_terminal',
            'redsys_environment',
            'currency', 'require_deposit', 'deposit_percentage',
            'success_url', 'cancel_url', 'notification_email',
        ]
        widgets = {
            'active_gateway': forms.Select(attrs={
                'class': 'select',
            }),
            'stripe_public_key': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'pk_live_...',
            }),
            'stripe_secret_key': forms.PasswordInput(attrs={
                'class': 'input',
                'placeholder': 'sk_live_...',
                'autocomplete': 'off',
            }),
            'stripe_webhook_secret': forms.PasswordInput(attrs={
                'class': 'input',
                'placeholder': 'whsec_...',
                'autocomplete': 'off',
            }),
            'redsys_merchant_code': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Merchant code'),
            }),
            'redsys_secret_key': forms.PasswordInput(attrs={
                'class': 'input',
                'placeholder': _('Secret key'),
                'autocomplete': 'off',
            }),
            'redsys_terminal': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': '001',
            }),
            'redsys_environment': forms.Select(attrs={
                'class': 'select',
            }),
            'currency': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'EUR',
                'maxlength': '3',
            }),
            'require_deposit': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'deposit_percentage': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
                'max': '100',
                'step': '0.01',
            }),
            'success_url': forms.URLInput(attrs={
                'class': 'input',
                'placeholder': 'https://',
            }),
            'cancel_url': forms.URLInput(attrs={
                'class': 'input',
                'placeholder': 'https://',
            }),
            'notification_email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': _('email@example.com'),
            }),
        }


class PaymentLinkForm(forms.ModelForm):
    """Form for creating and editing payment links."""

    class Meta:
        model = PaymentLink
        fields = [
            'title', 'description', 'amount', 'currency',
            'customer_email', 'expires_at', 'max_uses',
            'source_type', 'source_id',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Payment title'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': '3',
                'placeholder': _('Optional description'),
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0.01',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'currency': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'EUR',
                'maxlength': '3',
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': _('customer@example.com'),
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'input',
                'type': 'datetime-local',
            }),
            'max_uses': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
                'placeholder': _('1 (0 = unlimited)'),
            }),
            'source_type': forms.HiddenInput(),
            'source_id': forms.HiddenInput(),
        }
