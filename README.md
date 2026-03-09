# Online Payments

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `online_payments` |
| **Version** | `1.0.0` |
| **Icon** | `card-outline` |
| **Dependencies** | None |

## Models

### `PaymentGatewaySettings`

Per-hub payment gateway configuration.

| Field | Type | Details |
|-------|------|---------|
| `active_gateway` | CharField | max_length=20, choices: none, stripe, redsys, manual |
| `stripe_public_key` | CharField | max_length=255, optional |
| `stripe_secret_key` | CharField | max_length=255, optional |
| `stripe_webhook_secret` | CharField | max_length=255, optional |
| `redsys_merchant_code` | CharField | max_length=20, optional |
| `redsys_secret_key` | CharField | max_length=255, optional |
| `redsys_terminal` | CharField | max_length=5 |
| `redsys_environment` | CharField | max_length=20, choices: test, production |
| `currency` | CharField | max_length=3 |
| `require_deposit` | BooleanField |  |
| `deposit_percentage` | DecimalField |  |
| `success_url` | URLField | max_length=200, optional |
| `cancel_url` | URLField | max_length=200, optional |
| `notification_email` | EmailField | max_length=254, optional |

**Methods:**

- `get_settings()` — Get or create settings singleton for the given hub.

### `PaymentTransaction`

Payment transaction record.

| Field | Type | Details |
|-------|------|---------|
| `transaction_id` | CharField | max_length=100 |
| `gateway` | CharField | max_length=20 |
| `amount` | DecimalField |  |
| `currency` | CharField | max_length=3 |
| `status` | CharField | max_length=20, choices: pending, processing, completed, failed, refunded, partially_refunded |
| `gateway_reference` | CharField | max_length=255, optional |
| `payment_method_type` | CharField | max_length=50, optional |
| `customer_email` | EmailField | max_length=254, optional |
| `customer_name` | CharField | max_length=255, optional |
| `description` | TextField | optional |
| `source_type` | CharField | max_length=50, optional |
| `source_id` | UUIDField | max_length=32, optional |
| `metadata` | JSONField | optional |
| `error_message` | TextField | optional |
| `refund_amount` | DecimalField |  |
| `refunded_at` | DateTimeField | optional |
| `completed_at` | DateTimeField | optional |

**Methods:**

- `mark_completed()` — Mark the transaction as completed.
- `mark_failed()` — Mark the transaction as failed.
- `process_refund()` — Process a refund for this transaction.

Args:
    amount: Amount to refund. If None, refunds the full amount.

### `PaymentLink`

Shareable payment links for remote payments.

| Field | Type | Details |
|-------|------|---------|
| `title` | CharField | max_length=255 |
| `description` | TextField | optional |
| `amount` | DecimalField |  |
| `currency` | CharField | max_length=3 |
| `slug` | SlugField | max_length=50 |
| `is_active` | BooleanField |  |
| `expires_at` | DateTimeField | optional |
| `max_uses` | PositiveIntegerField |  |
| `current_uses` | PositiveIntegerField |  |
| `customer_email` | EmailField | max_length=254, optional |
| `source_type` | CharField | max_length=50, optional |
| `source_id` | UUIDField | max_length=32, optional |

**Properties:**

- `is_expired` — Check if the payment link has expired.
- `is_available` — Check if the payment link is available for use.
- `full_url` — Return the full public URL for this payment link.

## URL Endpoints

Base path: `/m/online_payments/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `dashboard` | GET |
| `payment_links/` | `payment_links` | GET |
| `transactions/` | `transactions` | GET |
| `transactions/<uuid:pk>/` | `transaction_detail` | GET |
| `transactions/<uuid:pk>/refund/` | `refund` | GET |
| `links/` | `payment_links` | GET |
| `links/create/` | `payment_link_create` | GET/POST |
| `links/<uuid:pk>/deactivate/` | `payment_link_deactivate` | GET |
| `links/<uuid:pk>/delete/` | `payment_link_delete` | GET/POST |
| `checkout/<slug:slug>/` | `checkout` | GET |
| `api/create-session/` | `api_create_session` | GET/POST |
| `api/webhook/` | `api_webhook` | GET |
| `settings/` | `settings` | GET |
| `settings/save/` | `settings_save` | GET/POST |

## Permissions

| Permission | Description |
|------------|-------------|
| `online_payments.view_transaction` | View Transaction |
| `online_payments.add_transaction` | Add Transaction |
| `online_payments.refund_transaction` | Refund Transaction |
| `online_payments.view_payment_link` | View Payment Link |
| `online_payments.add_payment_link` | Add Payment Link |
| `online_payments.delete_payment_link` | Delete Payment Link |
| `online_payments.manage_settings` | Manage Settings |

**Role assignments:**

- **admin**: All permissions
- **manager**: `add_payment_link`, `add_transaction`, `refund_transaction`, `view_payment_link`, `view_transaction`
- **employee**: `add_transaction`, `view_payment_link`, `view_transaction`

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Dashboard | `speedometer-outline` | `dashboard` | No |
| Transactions | `list-outline` | `transactions` | No |
| Payment Links | `link-outline` | `payment_links` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_payment_transactions`

List payment transactions.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | pending, processing, completed, failed, refunded |
| `gateway` | string | No |  |
| `limit` | integer | No |  |

### `list_payment_links`

List payment links.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `is_active` | boolean | No |  |

### `create_payment_link`

Create a payment link for customers.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes |  |
| `description` | string | No |  |
| `amount` | string | Yes |  |
| `currency` | string | No |  |
| `customer_email` | string | No |  |
| `expires_at` | string | No |  |

## File Structure

```
README.md
__init__.py
ai_tools.py
apps.py
forms.py
locale/
  es/
    LC_MESSAGES/
      django.po
migrations/
  0001_initial.py
  __init__.py
models.py
module.py
templates/
  online_payments/
    pages/
      checkout.html
      checkout_unavailable.html
      dashboard.html
      payment_link_form.html
      payment_links.html
      settings.html
      transaction_detail.html
      transactions.html
    partials/
      dashboard_content.html
      payment_link_form_content.html
      payment_links_content.html
      settings_content.html
      transaction_detail_content.html
      transactions_content.html
      transactions_table_body.html
tests/
  __init__.py
  conftest.py
  test_models.py
  test_views.py
urls.py
views.py
```
