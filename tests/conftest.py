"""
Pytest fixtures for online_payments module tests.
"""

import os
import uuid
import pytest
from decimal import Decimal
from datetime import timedelta
from django.test import Client
from django.utils import timezone


os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'


@pytest.fixture
def hub_id(hub_config):
    """Hub ID from HubConfig singleton."""
    return hub_config.hub_id


@pytest.fixture
def gateway_settings(hub_id):
    """Create PaymentGatewaySettings for the test hub."""
    from online_payments.models import PaymentGatewaySettings
    return PaymentGatewaySettings.get_settings(hub_id)


@pytest.fixture
def stripe_settings(hub_id):
    """Create Stripe-configured settings."""
    from online_payments.models import PaymentGatewaySettings
    settings = PaymentGatewaySettings.get_settings(hub_id)
    settings.active_gateway = 'stripe'
    settings.stripe_public_key = 'pk_test_123'
    settings.stripe_secret_key = 'sk_test_123'
    settings.stripe_webhook_secret = 'whsec_test_123'
    settings.save()
    return settings


@pytest.fixture
def redsys_settings(hub_id):
    """Create Redsys-configured settings."""
    from online_payments.models import PaymentGatewaySettings
    settings = PaymentGatewaySettings.get_settings(hub_id)
    settings.active_gateway = 'redsys'
    settings.redsys_merchant_code = '999008881'
    settings.redsys_secret_key = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
    settings.redsys_terminal = '001'
    settings.redsys_environment = 'test'
    settings.save()
    return settings


@pytest.fixture
def pending_transaction(hub_id):
    """Create a pending transaction."""
    from online_payments.models import PaymentTransaction
    return PaymentTransaction.objects.create(
        hub_id=hub_id,
        gateway='stripe',
        amount=Decimal('50.00'),
        currency='EUR',
        status='pending',
        customer_email='customer@example.com',
        customer_name='Test Customer',
        description='Test payment',
    )


@pytest.fixture
def completed_transaction(hub_id):
    """Create a completed transaction."""
    from online_payments.models import PaymentTransaction
    return PaymentTransaction.objects.create(
        hub_id=hub_id,
        gateway='stripe',
        amount=Decimal('100.00'),
        currency='EUR',
        status='completed',
        gateway_reference='pi_test_123',
        payment_method_type='card',
        customer_email='customer@example.com',
        customer_name='Completed Customer',
        description='Completed payment',
        completed_at=timezone.now(),
    )


@pytest.fixture
def failed_transaction(hub_id):
    """Create a failed transaction."""
    from online_payments.models import PaymentTransaction
    return PaymentTransaction.objects.create(
        hub_id=hub_id,
        gateway='stripe',
        amount=Decimal('75.00'),
        currency='EUR',
        status='failed',
        customer_name='Failed Customer',
        error_message='Card declined',
    )


@pytest.fixture
def active_payment_link(hub_id):
    """Create an active payment link."""
    from online_payments.models import PaymentLink
    return PaymentLink.objects.create(
        hub_id=hub_id,
        title='Test Payment',
        description='Test payment description',
        amount=Decimal('25.00'),
        currency='EUR',
        slug='test-pay-link',
        is_active=True,
        max_uses=5,
        current_uses=0,
    )


@pytest.fixture
def expired_payment_link(hub_id):
    """Create an expired payment link."""
    from online_payments.models import PaymentLink
    return PaymentLink.objects.create(
        hub_id=hub_id,
        title='Expired Payment',
        amount=Decimal('30.00'),
        currency='EUR',
        slug='expired-link',
        is_active=True,
        expires_at=timezone.now() - timedelta(hours=1),
    )


@pytest.fixture
def maxed_out_payment_link(hub_id):
    """Create a payment link that has reached max uses."""
    from online_payments.models import PaymentLink
    return PaymentLink.objects.create(
        hub_id=hub_id,
        title='Maxed Out',
        amount=Decimal('15.00'),
        currency='EUR',
        slug='maxed-link',
        is_active=True,
        max_uses=3,
        current_uses=3,
    )


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
def auth_client(employee, store_config):
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
