import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import HubBaseModel


# ---------------------------------------------------------------------------
# Payment Gateway Settings
# ---------------------------------------------------------------------------

class PaymentGatewaySettings(HubBaseModel):
    """Per-hub payment gateway configuration."""

    GATEWAY_CHOICES = [
        ('none', _('None')),
        ('stripe', _('Stripe')),
        ('redsys', _('Redsys')),
        ('manual', _('Manual')),
    ]

    REDSYS_ENVIRONMENT_CHOICES = [
        ('test', _('Test')),
        ('production', _('Production')),
    ]

    # Active gateway
    active_gateway = models.CharField(
        _('Active Gateway'),
        max_length=20,
        choices=GATEWAY_CHOICES,
        default='none',
    )

    # Stripe settings
    stripe_public_key = models.CharField(
        _('Stripe Public Key'),
        max_length=255,
        blank=True,
        default='',
    )
    stripe_secret_key = models.CharField(
        _('Stripe Secret Key'),
        max_length=255,
        blank=True,
        default='',
    )
    stripe_webhook_secret = models.CharField(
        _('Stripe Webhook Secret'),
        max_length=255,
        blank=True,
        default='',
    )

    # Redsys settings
    redsys_merchant_code = models.CharField(
        _('Redsys Merchant Code'),
        max_length=20,
        blank=True,
        default='',
    )
    redsys_secret_key = models.CharField(
        _('Redsys Secret Key'),
        max_length=255,
        blank=True,
        default='',
    )
    redsys_terminal = models.CharField(
        _('Redsys Terminal'),
        max_length=5,
        default='001',
    )
    redsys_environment = models.CharField(
        _('Redsys Environment'),
        max_length=20,
        choices=REDSYS_ENVIRONMENT_CHOICES,
        default='test',
    )

    # General settings
    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='EUR',
    )
    require_deposit = models.BooleanField(
        _('Require Deposit'),
        default=False,
        help_text=_('Require a deposit for appointments and orders.'),
    )
    deposit_percentage = models.DecimalField(
        _('Deposit Percentage'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Percentage of total to collect as deposit.'),
    )

    # URLs
    success_url = models.URLField(
        _('Success URL'),
        blank=True,
        default='',
        help_text=_('URL to redirect after successful payment.'),
    )
    cancel_url = models.URLField(
        _('Cancel URL'),
        blank=True,
        default='',
        help_text=_('URL to redirect after cancelled payment.'),
    )

    # Notifications
    notification_email = models.EmailField(
        _('Notification Email'),
        blank=True,
        default='',
        help_text=_('Email address for payment notifications.'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'online_payments_settings'
        verbose_name = _('Payment Gateway Settings')
        verbose_name_plural = _('Payment Gateway Settings')
        unique_together = [('hub_id',)]

    def __str__(self):
        return f"Payment Gateway Settings (hub {self.hub_id})"

    @classmethod
    def get_settings(cls, hub_id):
        """Get or create settings singleton for the given hub."""
        settings, _ = cls.all_objects.get_or_create(hub_id=hub_id)
        return settings


# ---------------------------------------------------------------------------
# Payment Transaction
# ---------------------------------------------------------------------------

class PaymentTransaction(HubBaseModel):
    """Payment transaction record."""

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('partially_refunded', _('Partially Refunded')),
    ]

    transaction_id = models.CharField(
        _('Transaction ID'),
        max_length=100,
        unique=True,
        help_text=_('Internal unique transaction identifier.'),
    )
    gateway = models.CharField(
        _('Gateway'),
        max_length=20,
        help_text=_('Payment gateway used for this transaction.'),
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=10,
        decimal_places=2,
    )
    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='EUR',
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    gateway_reference = models.CharField(
        _('Gateway Reference'),
        max_length=255,
        blank=True,
        default='',
        help_text=_('Gateway-specific transaction ID.'),
    )
    payment_method_type = models.CharField(
        _('Payment Method Type'),
        max_length=50,
        blank=True,
        default='',
        help_text=_('Payment method type (card/bizum/transfer).'),
    )

    # Customer info
    customer_email = models.EmailField(
        _('Customer Email'),
        blank=True,
        default='',
    )
    customer_name = models.CharField(
        _('Customer Name'),
        max_length=255,
        blank=True,
        default='',
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        default='',
    )

    # Source reference (what this payment is for)
    source_type = models.CharField(
        _('Source Type'),
        max_length=50,
        blank=True,
        default='',
        help_text=_('Source type (appointment/sale/invoice/link).'),
    )
    source_id = models.UUIDField(
        _('Source ID'),
        null=True,
        blank=True,
    )

    # Metadata
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
    )

    # Error handling
    error_message = models.TextField(
        _('Error Message'),
        blank=True,
        default='',
    )

    # Refund tracking
    refund_amount = models.DecimalField(
        _('Refund Amount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    refunded_at = models.DateTimeField(
        _('Refunded At'),
        null=True,
        blank=True,
    )

    # Completion
    completed_at = models.DateTimeField(
        _('Completed At'),
        null=True,
        blank=True,
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'online_payments_transaction'
        verbose_name = _('Payment Transaction')
        verbose_name_plural = _('Payment Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hub_id', 'status', '-created_at']),
            models.Index(fields=['hub_id', 'source_type', 'source_id']),
        ]

    def __str__(self):
        return f"Transaction {self.transaction_id} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self._generate_transaction_id()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_transaction_id():
        """Generate a unique transaction ID."""
        now = timezone.now()
        prefix = now.strftime('%Y%m%d%H%M%S')
        suffix = uuid.uuid4().hex[:8].upper()
        return f"TXN-{prefix}-{suffix}"

    def mark_completed(self):
        """Mark the transaction as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def mark_failed(self, error=''):
        """Mark the transaction as failed."""
        self.status = 'failed'
        self.error_message = error
        self.save(update_fields=['status', 'error_message', 'updated_at'])

    def process_refund(self, amount=None):
        """
        Process a refund for this transaction.

        Args:
            amount: Amount to refund. If None, refunds the full amount.
        """
        if amount is None:
            amount = self.amount

        amount = Decimal(str(amount))

        if amount <= Decimal('0.00'):
            raise ValueError(_('Refund amount must be positive.'))

        max_refundable = self.amount - self.refund_amount
        if amount > max_refundable:
            raise ValueError(
                _('Refund amount (%(amount)s) exceeds maximum refundable (%(max)s).')
                % {'amount': amount, 'max': max_refundable}
            )

        self.refund_amount += amount
        self.refunded_at = timezone.now()

        if self.refund_amount >= self.amount:
            self.status = 'refunded'
        else:
            self.status = 'partially_refunded'

        self.save(update_fields=[
            'refund_amount', 'refunded_at', 'status', 'updated_at',
        ])


# ---------------------------------------------------------------------------
# Payment Link
# ---------------------------------------------------------------------------

class PaymentLink(HubBaseModel):
    """Shareable payment links for remote payments."""

    title = models.CharField(
        _('Title'),
        max_length=255,
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        default='',
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=10,
        decimal_places=2,
    )
    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='EUR',
    )
    slug = models.SlugField(
        _('Slug'),
        unique=True,
        help_text=_('URL-friendly identifier for the payment link.'),
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
    )
    expires_at = models.DateTimeField(
        _('Expires At'),
        null=True,
        blank=True,
    )
    max_uses = models.PositiveIntegerField(
        _('Max Uses'),
        default=1,
        help_text=_('Maximum number of times this link can be used (0 = unlimited).'),
    )
    current_uses = models.PositiveIntegerField(
        _('Current Uses'),
        default=0,
    )
    customer_email = models.EmailField(
        _('Customer Email'),
        blank=True,
        default='',
    )

    # Source reference (what this link is for)
    source_type = models.CharField(
        _('Source Type'),
        max_length=50,
        blank=True,
        default='',
    )
    source_id = models.UUIDField(
        _('Source ID'),
        null=True,
        blank=True,
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'online_payments_link'
        verbose_name = _('Payment Link')
        verbose_name_plural = _('Payment Links')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.amount} {self.currency})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_slug()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_slug():
        """Generate a unique URL-safe slug."""
        return uuid.uuid4().hex[:12]

    @property
    def is_expired(self):
        """Check if the payment link has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_available(self):
        """Check if the payment link is available for use."""
        if not self.is_active:
            return False
        if self.is_expired:
            return False
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
        return True

    @property
    def full_url(self):
        """Return the full public URL for this payment link."""
        from django.urls import reverse
        return reverse('online_payments:checkout', kwargs={'slug': self.slug})
