# Online Payments Module

Payment gateway integration for online and remote payments.

## Features

- Multiple payment gateway support: Stripe, Redsys, and manual processing
- Full transaction lifecycle: pending, processing, completed, failed, refunded, partially refunded
- Auto-generated transaction IDs with timestamp prefix
- Full and partial refund processing with amount validation
- Shareable payment links with unique slugs for remote payments
- Payment link controls: expiration dates, usage limits, active/inactive state
- Deposit collection support with configurable percentage
- Source tracking to link transactions to appointments, sales, invoices, or payment links
- Customer info and metadata storage on transactions
- Configurable success and cancel redirect URLs
- Payment notification email support
- Redsys test and production environment switching

## Installation

This module is installed automatically via the ERPlora Marketplace.

## Configuration

Access settings via: **Menu > Online Payments > Settings**

Select the active payment gateway (Stripe, Redsys, or manual), enter gateway credentials, set the default currency, configure deposit requirements, and define redirect URLs and notification emails.

## Usage

Access via: **Menu > Online Payments**

### Views

| View | URL | Description |
|------|-----|-------------|
| Dashboard | `/m/online_payments/dashboard/` | Payment activity overview and statistics |
| Transactions | `/m/online_payments/transactions/` | List and manage payment transactions |
| Payment Links | `/m/online_payments/payment_links/` | Create and manage shareable payment links |
| Settings | `/m/online_payments/settings/` | Configure payment gateways and options |

## Models

| Model | Description |
|-------|-------------|
| `PaymentGatewaySettings` | Per-hub singleton with active gateway selection, Stripe/Redsys credentials, currency, deposit rules, and redirect URLs |
| `PaymentTransaction` | Payment record with transaction ID, gateway, amount, status, customer info, refund tracking, and source reference |
| `PaymentLink` | Shareable payment link with title, amount, slug, expiration, usage limits, and source reference |

## Permissions

| Permission | Description |
|------------|-------------|
| `online_payments.view_transaction` | View payment transactions |
| `online_payments.add_transaction` | Create new payment transactions |
| `online_payments.refund_transaction` | Process full or partial refunds |
| `online_payments.view_payment_link` | View payment links |
| `online_payments.add_payment_link` | Create new payment links |
| `online_payments.delete_payment_link` | Delete payment links |
| `online_payments.manage_settings` | Access and modify gateway settings |

## License

MIT

## Author

ERPlora Team - support@erplora.com
