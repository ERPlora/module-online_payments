# Generated migration for online_payments module

import uuid
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PaymentGatewaySettings',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('hub_id', models.UUIDField(blank=True, db_index=True, editable=False, help_text='Hub this record belongs to (for multi-tenancy)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, help_text='UUID of the user who created this record', null=True)),
                ('updated_by', models.UUIDField(blank=True, help_text='UUID of the user who last updated this record', null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False, help_text='Soft delete flag - record is hidden but not removed')),
                ('deleted_at', models.DateTimeField(blank=True, help_text='Timestamp when record was soft deleted', null=True)),
                ('active_gateway', models.CharField(choices=[('none', 'None'), ('stripe', 'Stripe'), ('redsys', 'Redsys'), ('manual', 'Manual')], default='none', max_length=20, verbose_name='Active Gateway')),
                ('stripe_public_key', models.CharField(blank=True, default='', max_length=255, verbose_name='Stripe Public Key')),
                ('stripe_secret_key', models.CharField(blank=True, default='', max_length=255, verbose_name='Stripe Secret Key')),
                ('stripe_webhook_secret', models.CharField(blank=True, default='', max_length=255, verbose_name='Stripe Webhook Secret')),
                ('redsys_merchant_code', models.CharField(blank=True, default='', max_length=20, verbose_name='Redsys Merchant Code')),
                ('redsys_secret_key', models.CharField(blank=True, default='', max_length=255, verbose_name='Redsys Secret Key')),
                ('redsys_terminal', models.CharField(default='001', max_length=5, verbose_name='Redsys Terminal')),
                ('redsys_environment', models.CharField(choices=[('test', 'Test'), ('production', 'Production')], default='test', max_length=20, verbose_name='Redsys Environment')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Currency')),
                ('require_deposit', models.BooleanField(default=False, help_text='Require a deposit for appointments and orders.', verbose_name='Require Deposit')),
                ('deposit_percentage', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Percentage of total to collect as deposit.', max_digits=5, verbose_name='Deposit Percentage')),
                ('success_url', models.URLField(blank=True, default='', help_text='URL to redirect after successful payment.', verbose_name='Success URL')),
                ('cancel_url', models.URLField(blank=True, default='', help_text='URL to redirect after cancelled payment.', verbose_name='Cancel URL')),
                ('notification_email', models.EmailField(blank=True, default='', help_text='Email address for payment notifications.', max_length=254, verbose_name='Notification Email')),
            ],
            options={
                'verbose_name': 'Payment Gateway Settings',
                'verbose_name_plural': 'Payment Gateway Settings',
                'db_table': 'online_payments_settings',
                'abstract': False,
                'unique_together': {('hub_id',)},
            },
        ),
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('hub_id', models.UUIDField(blank=True, db_index=True, editable=False, help_text='Hub this record belongs to (for multi-tenancy)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, help_text='UUID of the user who created this record', null=True)),
                ('updated_by', models.UUIDField(blank=True, help_text='UUID of the user who last updated this record', null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False, help_text='Soft delete flag - record is hidden but not removed')),
                ('deleted_at', models.DateTimeField(blank=True, help_text='Timestamp when record was soft deleted', null=True)),
                ('transaction_id', models.CharField(help_text='Internal unique transaction identifier.', max_length=100, unique=True, verbose_name='Transaction ID')),
                ('gateway', models.CharField(help_text='Payment gateway used for this transaction.', max_length=20, verbose_name='Gateway')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Amount')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Currency')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('refunded', 'Refunded'), ('partially_refunded', 'Partially Refunded')], default='pending', max_length=20, verbose_name='Status')),
                ('gateway_reference', models.CharField(blank=True, default='', help_text='Gateway-specific transaction ID.', max_length=255, verbose_name='Gateway Reference')),
                ('payment_method_type', models.CharField(blank=True, default='', help_text='Payment method type (card/bizum/transfer).', max_length=50, verbose_name='Payment Method Type')),
                ('customer_email', models.EmailField(blank=True, default='', max_length=254, verbose_name='Customer Email')),
                ('customer_name', models.CharField(blank=True, default='', max_length=255, verbose_name='Customer Name')),
                ('description', models.TextField(blank=True, default='', verbose_name='Description')),
                ('source_type', models.CharField(blank=True, default='', help_text='Source type (appointment/sale/invoice/link).', max_length=50, verbose_name='Source Type')),
                ('source_id', models.UUIDField(blank=True, null=True, verbose_name='Source ID')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadata')),
                ('error_message', models.TextField(blank=True, default='', verbose_name='Error Message')),
                ('refund_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Refund Amount')),
                ('refunded_at', models.DateTimeField(blank=True, null=True, verbose_name='Refunded At')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Completed At')),
            ],
            options={
                'verbose_name': 'Payment Transaction',
                'verbose_name_plural': 'Payment Transactions',
                'db_table': 'online_payments_transaction',
                'ordering': ['-created_at'],
                'abstract': False,
                'indexes': [
                    models.Index(fields=['hub_id', 'status', '-created_at'], name='online_pay_hub_id_status_idx'),
                    models.Index(fields=['hub_id', 'source_type', 'source_id'], name='online_pay_hub_id_source_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='PaymentLink',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('hub_id', models.UUIDField(blank=True, db_index=True, editable=False, help_text='Hub this record belongs to (for multi-tenancy)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, help_text='UUID of the user who created this record', null=True)),
                ('updated_by', models.UUIDField(blank=True, help_text='UUID of the user who last updated this record', null=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False, help_text='Soft delete flag - record is hidden but not removed')),
                ('deleted_at', models.DateTimeField(blank=True, help_text='Timestamp when record was soft deleted', null=True)),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(blank=True, default='', verbose_name='Description')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Amount')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Currency')),
                ('slug', models.SlugField(help_text='URL-friendly identifier for the payment link.', unique=True, verbose_name='Slug')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expires At')),
                ('max_uses', models.PositiveIntegerField(default=1, help_text='Maximum number of times this link can be used (0 = unlimited).', verbose_name='Max Uses')),
                ('current_uses', models.PositiveIntegerField(default=0, verbose_name='Current Uses')),
                ('customer_email', models.EmailField(blank=True, default='', max_length=254, verbose_name='Customer Email')),
                ('source_type', models.CharField(blank=True, default='', max_length=50, verbose_name='Source Type')),
                ('source_id', models.UUIDField(blank=True, null=True, verbose_name='Source ID')),
            ],
            options={
                'verbose_name': 'Payment Link',
                'verbose_name_plural': 'Payment Links',
                'db_table': 'online_payments_link',
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
    ]
