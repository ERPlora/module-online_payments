"""
AI context for the Online Payments module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Online Payments

### Models

**PaymentGatewaySettings** (singleton per hub)
- `active_gateway` — choices: none, stripe, redsys, manual
- Stripe fields: `stripe_public_key`, `stripe_secret_key`, `stripe_webhook_secret`
- Redsys fields: `redsys_merchant_code`, `redsys_secret_key`, `redsys_terminal`, `redsys_environment` (test/production)
- `currency` (default 'EUR')
- `require_deposit` (BooleanField), `deposit_percentage` (Decimal)
- `success_url`, `cancel_url` — redirect URLs after payment
- `notification_email` — email for payment alerts
- Use `PaymentGatewaySettings.get_settings(hub_id)` to get or create

**PaymentTransaction**
- `transaction_id` (CharField, unique) — auto-generated format: TXN-{YYYYMMDDHHMMSS}-{8 hex chars}
- `gateway` — which gateway processed the transaction (stripe/redsys/manual)
- `amount`, `currency` (Decimal)
- `status` — choices: pending, processing, completed, failed, refunded, partially_refunded
- `gateway_reference` — external transaction ID from the gateway
- `payment_method_type` — e.g. card, bizum, transfer
- `customer_email`, `customer_name`, `description`
- `source_type` (CharField) — what this payment is for: appointment, sale, invoice, link
- `source_id` (UUIDField) — UUID of the linked record
- `refund_amount`, `refunded_at`, `completed_at`, `error_message`
- `metadata` (JSONField) — arbitrary extra data

**PaymentLink**
- `title`, `description`, `amount`, `currency`
- `slug` (SlugField, unique) — auto-generated 12-char hex, used in checkout URL
- `is_active` (BooleanField, default True)
- `expires_at` (DateTimeField, nullable) — optional expiration
- `max_uses` (default 1, 0 = unlimited), `current_uses`
- `customer_email` — optional pre-fill
- `source_type`, `source_id` — link to the originating record (invoice, booking, etc.)

### Key flows

1. **Setup**: Configure `PaymentGatewaySettings` with active_gateway and credentials.
2. **Charge**: Create PaymentTransaction with status='pending', call gateway, then `.mark_completed()` or `.mark_failed(error)`.
3. **Refund**: Call `.process_refund(amount)` — auto-sets status to refunded or partially_refunded.
4. **Payment link**: Create PaymentLink with amount and title → share `full_url` → track `current_uses`.

### Relationships
- No direct FK to other models — uses `source_type` + `source_id` pattern to link to any record
- PaymentTransaction and PaymentLink both use `source_type`/`source_id` for cross-module references
"""
