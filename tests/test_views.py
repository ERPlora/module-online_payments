"""
Integration tests for Online Payments views.
"""

import json
import uuid
import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse


pytestmark = [pytest.mark.django_db, pytest.mark.unit]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_hub_config(db, settings):
    """Ensure HubConfig + StoreConfig exist."""
    from apps.configuration.models import HubConfig, StoreConfig
    config = HubConfig.get_solo()
    config.save()
    store = StoreConfig.get_solo()
    store.business_name = 'Test Business'
    store.is_configured = True
    store.save()


@pytest.fixture
def hub_id(db):
    from apps.configuration.models import HubConfig
    return HubConfig.get_solo().hub_id


@pytest.fixture
def employee(db):
    """Create a local user (employee)."""
    from apps.accounts.models import LocalUser
    return LocalUser.objects.create(
        name='Test Employee',
        email='employee@test.com',
        role='admin',
        is_active=True,
    )


@pytest.fixture
def auth_client(employee):
    """Authenticated Django test client."""
    client = Client()
    session = client.session
    session['local_user_id'] = str(employee.id)
    session['user_name'] = employee.name
    session['user_email'] = employee.email
    session['user_role'] = employee.role
    session['store_config_checked'] = True
    session.save()
    return client


@pytest.fixture
def gateway_settings(hub_id):
    from online_payments.models import PaymentGatewaySettings
    return PaymentGatewaySettings.get_settings(hub_id)


@pytest.fixture
def stripe_settings(hub_id):
    from online_payments.models import PaymentGatewaySettings
    settings = PaymentGatewaySettings.get_settings(hub_id)
    settings.active_gateway = 'stripe'
    settings.stripe_public_key = 'pk_test_123'
    settings.stripe_secret_key = 'sk_test_123'
    settings.save()
    return settings


@pytest.fixture
def completed_transaction(hub_id):
    from online_payments.models import PaymentTransaction
    from django.utils import timezone
    return PaymentTransaction.objects.create(
        hub_id=hub_id,
        gateway='stripe',
        amount=Decimal('100.00'),
        currency='EUR',
        status='completed',
        gateway_reference='pi_test_123',
        customer_name='Test Customer',
        customer_email='test@example.com',
        completed_at=timezone.now(),
    )


@pytest.fixture
def pending_transaction(hub_id):
    from online_payments.models import PaymentTransaction
    return PaymentTransaction.objects.create(
        hub_id=hub_id,
        gateway='stripe',
        amount=Decimal('50.00'),
        currency='EUR',
        status='pending',
        customer_name='Pending Customer',
    )


@pytest.fixture
def active_link(hub_id):
    from online_payments.models import PaymentLink
    return PaymentLink.objects.create(
        hub_id=hub_id,
        title='Test Link',
        amount=Decimal('25.00'),
        slug='test-link-001',
        is_active=True,
        max_uses=5,
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:

    def test_requires_login(self):
        client = Client()
        response = client.get('/m/online_payments/')
        assert response.status_code == 302

    def test_dashboard_loads(self, auth_client):
        response = auth_client.get('/m/online_payments/')
        assert response.status_code == 200

    def test_htmx_returns_partial(self, auth_client):
        response = auth_client.get('/m/online_payments/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_dashboard_with_transactions(self, auth_client, completed_transaction):
        response = auth_client.get('/m/online_payments/')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

class TestTransactions:

    def test_requires_login(self):
        client = Client()
        response = client.get('/m/online_payments/transactions/')
        assert response.status_code == 302

    def test_transactions_loads(self, auth_client):
        response = auth_client.get('/m/online_payments/transactions/')
        assert response.status_code == 200

    def test_htmx_returns_partial(self, auth_client):
        response = auth_client.get(
            '/m/online_payments/transactions/', HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200

    def test_search_filter(self, auth_client, completed_transaction):
        response = auth_client.get('/m/online_payments/transactions/?search=Test')
        assert response.status_code == 200

    def test_status_filter(self, auth_client, completed_transaction, pending_transaction):
        response = auth_client.get('/m/online_payments/transactions/?status=completed')
        assert response.status_code == 200

    def test_gateway_filter(self, auth_client, completed_transaction):
        response = auth_client.get('/m/online_payments/transactions/?gateway=stripe')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Transaction Detail
# ---------------------------------------------------------------------------

class TestTransactionDetail:

    def test_detail_loads(self, auth_client, completed_transaction):
        response = auth_client.get(
            f'/m/online_payments/transactions/{completed_transaction.pk}/',
        )
        assert response.status_code == 200

    def test_detail_not_found(self, auth_client):
        fake_uuid = uuid.uuid4()
        response = auth_client.get(f'/m/online_payments/transactions/{fake_uuid}/')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Refund
# ---------------------------------------------------------------------------

class TestRefund:

    def test_refund_full(self, auth_client, completed_transaction):
        response = auth_client.post(
            f'/m/online_payments/transactions/{completed_transaction.pk}/refund/',
            data=json.dumps({}),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True
        assert data['status'] == 'refunded'
        assert data['refund_amount'] == 100.0

    def test_refund_partial(self, auth_client, completed_transaction):
        response = auth_client.post(
            f'/m/online_payments/transactions/{completed_transaction.pk}/refund/',
            data=json.dumps({'amount': 30.0}),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True
        assert data['status'] == 'partially_refunded'
        assert data['refund_amount'] == 30.0

    def test_refund_pending_fails(self, auth_client, pending_transaction):
        response = auth_client.post(
            f'/m/online_payments/transactions/{pending_transaction.pk}/refund/',
            data=json.dumps({}),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is False

    def test_refund_exceed_amount_fails(self, auth_client, completed_transaction):
        response = auth_client.post(
            f'/m/online_payments/transactions/{completed_transaction.pk}/refund/',
            data=json.dumps({'amount': 200.0}),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is False

    def test_refund_not_found(self, auth_client):
        fake_uuid = uuid.uuid4()
        response = auth_client.post(
            f'/m/online_payments/transactions/{fake_uuid}/refund/',
            data=json.dumps({}),
            content_type='application/json',
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Payment Links
# ---------------------------------------------------------------------------

class TestPaymentLinks:

    def test_requires_login(self):
        client = Client()
        response = client.get('/m/online_payments/links/')
        assert response.status_code == 302

    def test_links_loads(self, auth_client):
        response = auth_client.get('/m/online_payments/links/')
        assert response.status_code == 200

    def test_links_with_data(self, auth_client, active_link):
        response = auth_client.get('/m/online_payments/links/')
        assert response.status_code == 200

    def test_search_links(self, auth_client, active_link):
        response = auth_client.get('/m/online_payments/links/?search=Test')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Payment Link Create
# ---------------------------------------------------------------------------

class TestPaymentLinkCreate:

    def test_form_loads(self, auth_client):
        response = auth_client.get('/m/online_payments/links/create/')
        assert response.status_code == 200

    def test_create_link(self, auth_client):
        from online_payments.models import PaymentLink
        response = auth_client.post(
            '/m/online_payments/links/create/',
            data={
                'title': 'New Link',
                'amount': '50.00',
                'currency': 'EUR',
                'max_uses': '1',
            },
        )
        # Should redirect after creation
        assert response.status_code in (200, 302)
        assert PaymentLink.objects.filter(title='New Link').exists()

    def test_create_link_missing_required(self, auth_client):
        from online_payments.models import PaymentLink
        response = auth_client.post(
            '/m/online_payments/links/create/',
            data={
                'title': '',
                'amount': '',
            },
        )
        # Should return form with errors, not create
        assert not PaymentLink.objects.filter(title='').exists()


# ---------------------------------------------------------------------------
# Payment Link Deactivate
# ---------------------------------------------------------------------------

class TestPaymentLinkDeactivate:

    def test_deactivate(self, auth_client, active_link):
        response = auth_client.post(
            f'/m/online_payments/links/{active_link.pk}/deactivate/',
        )
        data = response.json()
        assert data['success'] is True
        active_link.refresh_from_db()
        assert active_link.is_active is False

    def test_deactivate_not_found(self, auth_client):
        fake_uuid = uuid.uuid4()
        response = auth_client.post(
            f'/m/online_payments/links/{fake_uuid}/deactivate/',
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Payment Link Delete
# ---------------------------------------------------------------------------

class TestPaymentLinkDelete:

    def test_delete(self, auth_client, active_link):
        from online_payments.models import PaymentLink
        response = auth_client.post(
            f'/m/online_payments/links/{active_link.pk}/delete/',
        )
        data = response.json()
        assert data['success'] is True
        assert PaymentLink.objects.filter(pk=active_link.pk).count() == 0

    def test_delete_not_found(self, auth_client):
        fake_uuid = uuid.uuid4()
        response = auth_client.post(
            f'/m/online_payments/links/{fake_uuid}/delete/',
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Checkout (Public)
# ---------------------------------------------------------------------------

class TestCheckout:

    def test_checkout_loads(self, active_link, gateway_settings):
        """Checkout page does not require login."""
        client = Client()
        response = client.get(f'/m/online_payments/checkout/{active_link.slug}/')
        assert response.status_code == 200

    def test_checkout_unavailable_expired(self, gateway_settings):
        from online_payments.models import PaymentLink
        from datetime import timedelta
        from django.utils import timezone as tz
        client = Client()
        link = PaymentLink.objects.create(
            hub_id=gateway_settings.hub_id,
            title='Expired',
            amount=Decimal('10.00'),
            slug='checkout-expired-test',
            is_active=True,
            expires_at=tz.now() - timedelta(hours=1),
        )
        response = client.get(f'/m/online_payments/checkout/{link.slug}/')
        assert response.status_code == 200
        # Should render unavailable template

    def test_checkout_unavailable_inactive(self, gateway_settings):
        from online_payments.models import PaymentLink
        link = PaymentLink.objects.create(
            hub_id=gateway_settings.hub_id,
            title='Inactive',
            amount=Decimal('10.00'),
            slug='checkout-inactive-test',
            is_active=False,
        )
        client = Client()
        response = client.get(f'/m/online_payments/checkout/{link.slug}/')
        assert response.status_code == 200

    def test_checkout_not_found(self):
        client = Client()
        response = client.get('/m/online_payments/checkout/nonexistent-slug/')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestSettingsView:

    def test_requires_login(self):
        client = Client()
        response = client.get('/m/online_payments/settings/')
        assert response.status_code == 302

    def test_settings_loads(self, auth_client):
        response = auth_client.get('/m/online_payments/settings/')
        assert response.status_code == 200

    def test_save_gateway(self, auth_client, hub_id, gateway_settings):
        from online_payments.models import PaymentGatewaySettings
        response = auth_client.post(
            '/m/online_payments/settings/save/',
            data=json.dumps({
                'active_gateway': 'stripe',
                'stripe_public_key': 'pk_test_new',
                'stripe_secret_key': 'sk_test_new',
                'currency': 'USD',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        refreshed = PaymentGatewaySettings.get_settings(hub_id)
        assert refreshed.active_gateway == 'stripe'
        assert refreshed.stripe_public_key == 'pk_test_new'
        assert refreshed.currency == 'USD'

    def test_save_redsys_settings(self, auth_client, hub_id, gateway_settings):
        from online_payments.models import PaymentGatewaySettings
        response = auth_client.post(
            '/m/online_payments/settings/save/',
            data=json.dumps({
                'active_gateway': 'redsys',
                'redsys_merchant_code': '999008881',
                'redsys_secret_key': 'testsecret',
                'redsys_terminal': '002',
                'redsys_environment': 'production',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True

        refreshed = PaymentGatewaySettings.get_settings(hub_id)
        assert refreshed.active_gateway == 'redsys'
        assert refreshed.redsys_merchant_code == '999008881'
        assert refreshed.redsys_terminal == '002'
        assert refreshed.redsys_environment == 'production'

    def test_save_deposit_settings(self, auth_client, hub_id, gateway_settings):
        from online_payments.models import PaymentGatewaySettings
        response = auth_client.post(
            '/m/online_payments/settings/save/',
            data=json.dumps({
                'active_gateway': 'none',
                'require_deposit': True,
                'deposit_percentage': '25.00',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True

        refreshed = PaymentGatewaySettings.get_settings(hub_id)
        assert refreshed.require_deposit is True
        assert refreshed.deposit_percentage == Decimal('25.00')

    def test_save_requires_login(self):
        client = Client()
        response = client.post(
            '/m/online_payments/settings/save/',
            data=json.dumps({'active_gateway': 'stripe'}),
            content_type='application/json',
        )
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------

class TestWebhook:

    def test_webhook_stripe_complete(self, completed_transaction):
        """Test Stripe webhook for completed checkout."""
        client = Client()
        # Reset to pending for the test
        completed_transaction.status = 'pending'
        completed_transaction.completed_at = None
        completed_transaction.save()

        response = client.post(
            '/m/online_payments/api/webhook/',
            data=json.dumps({
                'gateway': 'stripe',
                'type': 'checkout.session.completed',
                'data': {
                    'object': {
                        'metadata': {
                            'transaction_id': completed_transaction.transaction_id,
                        },
                        'payment_intent': 'pi_webhook_test',
                        'payment_method_types': ['card'],
                    },
                },
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['received'] is True

        completed_transaction.refresh_from_db()
        assert completed_transaction.status == 'completed'
        assert completed_transaction.gateway_reference == 'pi_webhook_test'

    def test_webhook_unknown_gateway(self):
        client = Client()
        response = client.post(
            '/m/online_payments/api/webhook/',
            data=json.dumps({'gateway': 'unknown'}),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_webhook_invalid_json(self):
        client = Client()
        response = client.post(
            '/m/online_payments/api/webhook/',
            data='not json',
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_webhook_csrf_exempt(self):
        """Webhook should not require CSRF token."""
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            '/m/online_payments/api/webhook/',
            data=json.dumps({'gateway': 'unknown'}),
            content_type='application/json',
        )
        # Should not get 403 CSRF error
        assert response.status_code != 403


# ---------------------------------------------------------------------------
# API Create Session
# ---------------------------------------------------------------------------

class TestAPICreateSession:

    def test_requires_login(self):
        client = Client()
        response = client.post(
            '/m/online_payments/api/create-session/',
            data=json.dumps({'amount': 10}),
            content_type='application/json',
        )
        assert response.status_code == 302

    def test_no_gateway_configured(self, auth_client, gateway_settings):
        response = auth_client.post(
            '/m/online_payments/api/create-session/',
            data=json.dumps({
                'amount': 25.00,
                'currency': 'EUR',
                'description': 'Test',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is False
        assert 'gateway' in data['error'].lower()

    def test_create_stripe_session(self, auth_client, stripe_settings):
        response = auth_client.post(
            '/m/online_payments/api/create-session/',
            data=json.dumps({
                'amount': 50.00,
                'currency': 'EUR',
                'description': 'Test payment',
                'customer_email': 'test@example.com',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is True
        assert 'transaction_id' in data
        assert data['gateway'] == 'stripe'

    def test_zero_amount_fails(self, auth_client, stripe_settings):
        response = auth_client.post(
            '/m/online_payments/api/create-session/',
            data=json.dumps({
                'amount': 0,
                'currency': 'EUR',
            }),
            content_type='application/json',
        )
        data = response.json()
        assert data['success'] is False
