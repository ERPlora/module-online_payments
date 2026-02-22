"""
Unit tests for Online Payments models.
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone


pytestmark = [pytest.mark.django_db, pytest.mark.unit]


# ---------------------------------------------------------------------------
# PaymentGatewaySettings
# ---------------------------------------------------------------------------

class TestPaymentGatewaySettings:
    """Tests for PaymentGatewaySettings model."""

    def test_get_settings_creates_singleton(self, hub_id):
        from online_payments.models import PaymentGatewaySettings
        s = PaymentGatewaySettings.get_settings(hub_id)
        assert s is not None
        assert s.hub_id == hub_id

    def test_get_settings_returns_existing(self, hub_id):
        from online_payments.models import PaymentGatewaySettings
        s1 = PaymentGatewaySettings.get_settings(hub_id)
        s2 = PaymentGatewaySettings.get_settings(hub_id)
        assert s1.pk == s2.pk

    def test_default_gateway_is_none(self, gateway_settings):
        assert gateway_settings.active_gateway == 'none'

    def test_default_currency(self, gateway_settings):
        assert gateway_settings.currency == 'EUR'

    def test_default_deposit_settings(self, gateway_settings):
        assert gateway_settings.require_deposit is False
        assert gateway_settings.deposit_percentage == Decimal('0.00')

    def test_default_stripe_keys_empty(self, gateway_settings):
        assert gateway_settings.stripe_public_key == ''
        assert gateway_settings.stripe_secret_key == ''
        assert gateway_settings.stripe_webhook_secret == ''

    def test_default_redsys_settings(self, gateway_settings):
        assert gateway_settings.redsys_merchant_code == ''
        assert gateway_settings.redsys_secret_key == ''
        assert gateway_settings.redsys_terminal == '001'
        assert gateway_settings.redsys_environment == 'test'

    def test_default_urls_empty(self, gateway_settings):
        assert gateway_settings.success_url == ''
        assert gateway_settings.cancel_url == ''

    def test_default_notification_email_empty(self, gateway_settings):
        assert gateway_settings.notification_email == ''

    def test_str(self, gateway_settings):
        assert 'Payment Gateway Settings' in str(gateway_settings)

    def test_update_to_stripe(self, gateway_settings):
        from online_payments.models import PaymentGatewaySettings
        gateway_settings.active_gateway = 'stripe'
        gateway_settings.stripe_public_key = 'pk_test_abc'
        gateway_settings.stripe_secret_key = 'sk_test_abc'
        gateway_settings.save()

        refreshed = PaymentGatewaySettings.get_settings(gateway_settings.hub_id)
        assert refreshed.active_gateway == 'stripe'
        assert refreshed.stripe_public_key == 'pk_test_abc'

    def test_update_to_redsys(self, gateway_settings):
        from online_payments.models import PaymentGatewaySettings
        gateway_settings.active_gateway = 'redsys'
        gateway_settings.redsys_merchant_code = '123456789'
        gateway_settings.redsys_environment = 'production'
        gateway_settings.save()

        refreshed = PaymentGatewaySettings.get_settings(gateway_settings.hub_id)
        assert refreshed.active_gateway == 'redsys'
        assert refreshed.redsys_merchant_code == '123456789'
        assert refreshed.redsys_environment == 'production'

    def test_all_gateway_choices(self, hub_id):
        from online_payments.models import PaymentGatewaySettings
        for choice, _ in PaymentGatewaySettings.GATEWAY_CHOICES:
            settings = PaymentGatewaySettings.get_settings(hub_id)
            settings.active_gateway = choice
            settings.save()
            assert settings.active_gateway == choice

    def test_deposit_percentage_update(self, gateway_settings):
        from online_payments.models import PaymentGatewaySettings
        gateway_settings.require_deposit = True
        gateway_settings.deposit_percentage = Decimal('25.50')
        gateway_settings.save()

        refreshed = PaymentGatewaySettings.get_settings(gateway_settings.hub_id)
        assert refreshed.require_deposit is True
        assert refreshed.deposit_percentage == Decimal('25.50')


# ---------------------------------------------------------------------------
# PaymentTransaction
# ---------------------------------------------------------------------------

class TestPaymentTransaction:
    """Tests for PaymentTransaction model."""

    def test_auto_transaction_id(self, hub_id):
        from online_payments.models import PaymentTransaction
        txn = PaymentTransaction.objects.create(
            hub_id=hub_id, gateway='stripe', amount=Decimal('10.00'),
        )
        assert txn.transaction_id.startswith('TXN-')

    def test_unique_transaction_ids(self, hub_id):
        from online_payments.models import PaymentTransaction
        t1 = PaymentTransaction.objects.create(
            hub_id=hub_id, gateway='stripe', amount=Decimal('10.00'),
        )
        t2 = PaymentTransaction.objects.create(
            hub_id=hub_id, gateway='stripe', amount=Decimal('20.00'),
        )
        assert t1.transaction_id != t2.transaction_id

    def test_default_status(self, hub_id):
        from online_payments.models import PaymentTransaction
        txn = PaymentTransaction.objects.create(
            hub_id=hub_id, gateway='stripe', amount=Decimal('10.00'),
        )
        assert txn.status == 'pending'

    def test_default_values(self, pending_transaction):
        assert pending_transaction.refund_amount == Decimal('0.00')
        assert pending_transaction.refunded_at is None
        assert pending_transaction.completed_at is None
        assert pending_transaction.error_message == ''
        assert pending_transaction.metadata == {}

    def test_str(self, pending_transaction):
        result = str(pending_transaction)
        assert pending_transaction.transaction_id in result
        assert 'pending' in result

    def test_mark_completed(self, pending_transaction):
        pending_transaction.mark_completed()
        pending_transaction.refresh_from_db()
        assert pending_transaction.status == 'completed'
        assert pending_transaction.completed_at is not None

    def test_mark_failed(self, pending_transaction):
        pending_transaction.mark_failed('Card declined')
        pending_transaction.refresh_from_db()
        assert pending_transaction.status == 'failed'
        assert pending_transaction.error_message == 'Card declined'

    def test_process_full_refund(self, completed_transaction):
        completed_transaction.process_refund()
        completed_transaction.refresh_from_db()
        assert completed_transaction.status == 'refunded'
        assert completed_transaction.refund_amount == Decimal('100.00')
        assert completed_transaction.refunded_at is not None

    def test_process_partial_refund(self, completed_transaction):
        completed_transaction.process_refund(Decimal('40.00'))
        completed_transaction.refresh_from_db()
        assert completed_transaction.status == 'partially_refunded'
        assert completed_transaction.refund_amount == Decimal('40.00')

    def test_process_multiple_partial_refunds(self, completed_transaction):
        completed_transaction.process_refund(Decimal('30.00'))
        completed_transaction.process_refund(Decimal('70.00'))
        completed_transaction.refresh_from_db()
        assert completed_transaction.status == 'refunded'
        assert completed_transaction.refund_amount == Decimal('100.00')

    def test_refund_exceeds_amount_raises(self, completed_transaction):
        with pytest.raises(ValueError):
            completed_transaction.process_refund(Decimal('150.00'))

    def test_refund_zero_raises(self, completed_transaction):
        with pytest.raises(ValueError):
            completed_transaction.process_refund(Decimal('0.00'))

    def test_refund_negative_raises(self, completed_transaction):
        with pytest.raises(ValueError):
            completed_transaction.process_refund(Decimal('-10.00'))

    def test_partial_then_exceed_raises(self, completed_transaction):
        completed_transaction.process_refund(Decimal('80.00'))
        with pytest.raises(ValueError):
            completed_transaction.process_refund(Decimal('30.00'))

    def test_all_statuses(self, hub_id):
        from online_payments.models import PaymentTransaction
        for status, _ in PaymentTransaction.STATUS_CHOICES:
            txn = PaymentTransaction.objects.create(
                hub_id=hub_id, gateway='stripe',
                amount=Decimal('10.00'), status=status,
            )
            assert txn.status == status

    def test_ordering_newest_first(self, hub_id):
        from online_payments.models import PaymentTransaction
        t1 = PaymentTransaction.objects.create(
            hub_id=hub_id, gateway='stripe', amount=Decimal('10.00'),
        )
        t2 = PaymentTransaction.objects.create(
            hub_id=hub_id, gateway='stripe', amount=Decimal('20.00'),
        )
        txns = list(PaymentTransaction.objects.filter(hub_id=hub_id))
        assert txns[0].pk == t2.pk
        assert txns[1].pk == t1.pk

    def test_indexes(self):
        from online_payments.models import PaymentTransaction
        index_fields = [idx.fields for idx in PaymentTransaction._meta.indexes]
        assert ['hub_id', 'status', '-created_at'] in index_fields
        assert ['hub_id', 'source_type', 'source_id'] in index_fields

    def test_soft_delete(self, pending_transaction):
        from online_payments.models import PaymentTransaction
        pending_transaction.delete()
        assert pending_transaction.is_deleted is True
        assert PaymentTransaction.objects.filter(pk=pending_transaction.pk).count() == 0
        assert PaymentTransaction.all_objects.filter(pk=pending_transaction.pk).count() == 1

    def test_source_reference(self, hub_id):
        from online_payments.models import PaymentTransaction
        import uuid
        source_uuid = uuid.uuid4()
        txn = PaymentTransaction.objects.create(
            hub_id=hub_id, gateway='stripe',
            amount=Decimal('50.00'),
            source_type='appointment',
            source_id=source_uuid,
        )
        assert txn.source_type == 'appointment'
        assert txn.source_id == source_uuid

    def test_metadata_json(self, hub_id):
        from online_payments.models import PaymentTransaction
        txn = PaymentTransaction.objects.create(
            hub_id=hub_id, gateway='stripe',
            amount=Decimal('10.00'),
            metadata={'payment_link_slug': 'abc123', 'extra': 'data'},
        )
        assert txn.metadata['payment_link_slug'] == 'abc123'
        assert txn.metadata['extra'] == 'data'


# ---------------------------------------------------------------------------
# PaymentLink
# ---------------------------------------------------------------------------

class TestPaymentLink:
    """Tests for PaymentLink model."""

    def test_create(self, active_payment_link):
        assert active_payment_link.title == 'Test Payment'
        assert active_payment_link.amount == Decimal('25.00')
        assert active_payment_link.is_active is True
        assert active_payment_link.slug == 'test-pay-link'

    def test_auto_slug(self, hub_id):
        from online_payments.models import PaymentLink
        link = PaymentLink.objects.create(
            hub_id=hub_id,
            title='Auto Slug',
            amount=Decimal('10.00'),
        )
        assert link.slug != ''
        assert len(link.slug) == 12

    def test_str(self, active_payment_link):
        result = str(active_payment_link)
        assert 'Test Payment' in result
        assert '25.00' in result

    def test_is_available_active(self, active_payment_link):
        assert active_payment_link.is_available is True

    def test_is_available_inactive(self, active_payment_link):
        active_payment_link.is_active = False
        active_payment_link.save()
        assert active_payment_link.is_available is False

    def test_is_expired_false(self, active_payment_link):
        assert active_payment_link.is_expired is False

    def test_is_expired_true(self, expired_payment_link):
        assert expired_payment_link.is_expired is True

    def test_is_expired_no_expiry(self, hub_id):
        from online_payments.models import PaymentLink
        link = PaymentLink.objects.create(
            hub_id=hub_id, title='No Expiry',
            amount=Decimal('10.00'), expires_at=None,
        )
        assert link.is_expired is False

    def test_is_available_expired(self, expired_payment_link):
        assert expired_payment_link.is_available is False

    def test_max_uses_reached(self, maxed_out_payment_link):
        assert maxed_out_payment_link.is_available is False

    def test_max_uses_unlimited(self, hub_id):
        from online_payments.models import PaymentLink
        link = PaymentLink.objects.create(
            hub_id=hub_id, title='Unlimited',
            amount=Decimal('10.00'), max_uses=0, current_uses=999,
        )
        assert link.is_available is True

    def test_full_url(self, active_payment_link):
        url = active_payment_link.full_url
        assert 'checkout' in url
        assert active_payment_link.slug in url

    def test_ordering_newest_first(self, hub_id):
        from online_payments.models import PaymentLink
        l1 = PaymentLink.objects.create(
            hub_id=hub_id, title='First', amount=Decimal('10.00'),
        )
        l2 = PaymentLink.objects.create(
            hub_id=hub_id, title='Second', amount=Decimal('20.00'),
        )
        links = list(PaymentLink.objects.filter(hub_id=hub_id))
        assert links[0].pk == l2.pk
        assert links[1].pk == l1.pk

    def test_soft_delete(self, active_payment_link):
        from online_payments.models import PaymentLink
        active_payment_link.delete()
        assert active_payment_link.is_deleted is True
        assert PaymentLink.objects.filter(pk=active_payment_link.pk).count() == 0
        assert PaymentLink.all_objects.filter(pk=active_payment_link.pk).count() == 1

    def test_increment_uses(self, active_payment_link):
        assert active_payment_link.current_uses == 0
        active_payment_link.current_uses += 1
        active_payment_link.save()
        active_payment_link.refresh_from_db()
        assert active_payment_link.current_uses == 1

    def test_source_reference(self, hub_id):
        from online_payments.models import PaymentLink
        import uuid
        source_uuid = uuid.uuid4()
        link = PaymentLink.objects.create(
            hub_id=hub_id, title='Linked',
            amount=Decimal('10.00'),
            source_type='invoice',
            source_id=source_uuid,
        )
        assert link.source_type == 'invoice'
        assert link.source_id == source_uuid
