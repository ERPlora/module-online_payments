"""AI tools for the Online Payments module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListPaymentTransactions(AssistantTool):
    name = "list_payment_transactions"
    description = "List payment transactions."
    module_id = "online_payments"
    required_permission = "online_payments.view_paymenttransaction"
    parameters = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "pending, processing, completed, failed, refunded"},
            "gateway": {"type": "string"}, "limit": {"type": "integer"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from online_payments.models import PaymentTransaction
        qs = PaymentTransaction.objects.all()
        if args.get('status'):
            qs = qs.filter(status=args['status'])
        if args.get('gateway'):
            qs = qs.filter(gateway=args['gateway'])
        limit = args.get('limit', 20)
        return {"transactions": [{"id": str(t.id), "transaction_id": t.transaction_id, "gateway": t.gateway, "amount": str(t.amount), "currency": t.currency, "status": t.status, "customer_name": t.customer_name, "created_at": t.created_at.isoformat()} for t in qs.order_by('-created_at')[:limit]]}


@register_tool
class ListPaymentLinks(AssistantTool):
    name = "list_payment_links"
    description = "List payment links."
    module_id = "online_payments"
    required_permission = "online_payments.view_paymentlink"
    parameters = {
        "type": "object",
        "properties": {"is_active": {"type": "boolean"}},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from online_payments.models import PaymentLink
        qs = PaymentLink.objects.all()
        if 'is_active' in args:
            qs = qs.filter(is_active=args['is_active'])
        return {"links": [{"id": str(l.id), "title": l.title, "amount": str(l.amount), "currency": l.currency, "slug": l.slug, "is_active": l.is_active, "current_uses": l.current_uses} for l in qs]}


@register_tool
class CreatePaymentLink(AssistantTool):
    name = "create_payment_link"
    description = "Create a payment link for customers."
    module_id = "online_payments"
    required_permission = "online_payments.add_paymentlink"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string"}, "description": {"type": "string"},
            "amount": {"type": "string"}, "currency": {"type": "string"},
            "customer_email": {"type": "string"}, "expires_at": {"type": "string"},
        },
        "required": ["title", "amount"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from online_payments.models import PaymentLink
        l = PaymentLink.objects.create(title=args['title'], description=args.get('description', ''), amount=Decimal(args['amount']), currency=args.get('currency', 'EUR'), customer_email=args.get('customer_email', ''), expires_at=args.get('expires_at'))
        return {"id": str(l.id), "slug": l.slug, "created": True}
