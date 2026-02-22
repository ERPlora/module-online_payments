import json
from decimal import Decimal

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import login_required
from apps.core.htmx import htmx_view
from apps.modules_runtime.navigation import with_module_nav

from .models import PaymentGatewaySettings, PaymentTransaction, PaymentLink
from .forms import PaymentGatewaySettingsForm, PaymentLinkForm


def _hub_id(request):
    return request.session.get('hub_id')


# ============================================================================
# Dashboard
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('online_payments', 'dashboard')
@htmx_view(
    'online_payments/pages/dashboard.html',
    'online_payments/partials/dashboard_content.html',
)
def dashboard(request):
    hub = _hub_id(request)
    today = timezone.now().date()

    base_qs = PaymentTransaction.objects.filter(
        hub_id=hub, is_deleted=False,
    )

    # Totals
    completed_qs = base_qs.filter(status='completed')
    total_collected = completed_qs.aggregate(
        s=Sum('amount'),
    )['s'] or Decimal('0.00')

    pending_qs = base_qs.filter(status='pending')
    total_pending = pending_qs.aggregate(
        s=Sum('amount'),
    )['s'] or Decimal('0.00')

    total_refunded = completed_qs.aggregate(
        s=Sum('refund_amount'),
    )['s'] or Decimal('0.00')

    # Today stats
    today_qs = completed_qs.filter(completed_at__date=today)
    collected_today = today_qs.aggregate(
        s=Sum('amount'),
    )['s'] or Decimal('0.00')

    # Recent transactions
    recent_transactions = base_qs.order_by('-created_at')[:10]

    # Active payment links count
    active_links_count = PaymentLink.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True,
    ).count()

    # Settings
    settings = PaymentGatewaySettings.get_settings(hub)

    return {
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_refunded': total_refunded,
        'collected_today': collected_today,
        'recent_transactions': recent_transactions,
        'active_links_count': active_links_count,
        'gateway_settings': settings,
    }


# ============================================================================
# Transactions
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('online_payments', 'transactions')
@htmx_view(
    'online_payments/pages/transactions.html',
    'online_payments/partials/transactions_content.html',
)
def transactions(request):
    hub = _hub_id(request)

    queryset = PaymentTransaction.objects.filter(
        hub_id=hub, is_deleted=False,
    )

    # Filters
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(transaction_id__icontains=search)
            | Q(customer_name__icontains=search)
            | Q(customer_email__icontains=search)
            | Q(gateway_reference__icontains=search)
        )

    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)

    gateway = request.GET.get('gateway', '')
    if gateway:
        queryset = queryset.filter(gateway=gateway)

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    queryset = queryset.order_by('-created_at')

    # Pagination
    from django.core.paginator import Paginator
    per_page = int(request.GET.get('per_page', 25))
    paginator = Paginator(queryset, per_page)
    page_num = int(request.GET.get('page', 1))
    page_obj = paginator.get_page(page_num)

    # HTMX table-only requests
    if request.headers.get('HX-Target') == 'transactions-table-container':
        return render(request, 'online_payments/partials/transactions_table_body.html', {
            'transactions': page_obj.object_list,
            'page_obj': page_obj,
            'search': search,
            'status_filter': status,
            'gateway_filter': gateway,
        })

    return {
        'transactions': page_obj.object_list,
        'page_obj': page_obj,
        'search': search,
        'status_filter': status,
        'gateway_filter': gateway,
    }


@require_http_methods(["GET"])
@login_required
@with_module_nav('online_payments', 'transactions')
@htmx_view(
    'online_payments/pages/transaction_detail.html',
    'online_payments/partials/transaction_detail_content.html',
)
def transaction_detail(request, pk):
    hub = _hub_id(request)
    transaction = get_object_or_404(
        PaymentTransaction,
        id=pk, hub_id=hub, is_deleted=False,
    )

    return {
        'transaction': transaction,
    }


@require_http_methods(["POST"])
@login_required
def refund(request, pk):
    """Process a refund for a transaction."""
    hub = _hub_id(request)

    try:
        transaction = get_object_or_404(
            PaymentTransaction,
            id=pk, hub_id=hub, is_deleted=False,
        )

        if transaction.status not in ('completed', 'partially_refunded'):
            return JsonResponse({
                'success': False,
                'error': str(_('Only completed transactions can be refunded.')),
            })

        body = json.loads(request.body) if request.body else {}
        amount = body.get('amount')

        if amount is not None:
            amount = Decimal(str(amount))

        transaction.process_refund(amount)

        return JsonResponse({
            'success': True,
            'status': transaction.status,
            'refund_amount': float(transaction.refund_amount),
        })
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# Payment Links
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('online_payments', 'payment_links')
@htmx_view(
    'online_payments/pages/payment_links.html',
    'online_payments/partials/payment_links_content.html',
)
def payment_links(request):
    hub = _hub_id(request)

    queryset = PaymentLink.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('-created_at')

    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(customer_email__icontains=search)
            | Q(slug__icontains=search)
        )

    return {
        'payment_links': queryset,
        'link_form': PaymentLinkForm(),
    }


@require_http_methods(["GET", "POST"])
@login_required
@with_module_nav('online_payments', 'payment_links')
@htmx_view(
    'online_payments/pages/payment_link_form.html',
    'online_payments/partials/payment_link_form_content.html',
)
def payment_link_create(request):
    hub = _hub_id(request)

    if request.method == 'POST':
        form = PaymentLinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.hub_id = hub
            link.save()

            if request.headers.get('HX-Request') == 'true':
                from django.http import HttpResponse
                response = HttpResponse()
                response['HX-Redirect'] = '/m/online_payments/links/'
                return response

            from django.shortcuts import redirect
            return redirect('online_payments:payment_links')
        else:
            return {'form': form}

    return {
        'form': PaymentLinkForm(),
    }


@require_http_methods(["POST"])
@login_required
def payment_link_deactivate(request, pk):
    """Deactivate a payment link."""
    hub = _hub_id(request)

    try:
        link = get_object_or_404(
            PaymentLink,
            id=pk, hub_id=hub, is_deleted=False,
        )
        link.is_active = False
        link.save(update_fields=['is_active', 'updated_at'])

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def payment_link_delete(request, pk):
    """Soft delete a payment link."""
    hub = _hub_id(request)

    try:
        link = get_object_or_404(
            PaymentLink,
            id=pk, hub_id=hub, is_deleted=False,
        )
        link.delete()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# Checkout (Public)
# ============================================================================

@require_http_methods(["GET"])
def checkout(request, slug):
    """Public checkout page for a payment link. No login required."""
    link = get_object_or_404(
        PaymentLink,
        slug=slug, is_deleted=False,
    )

    if not link.is_available:
        return render(request, 'online_payments/pages/checkout_unavailable.html', {
            'link': link,
        })

    settings = PaymentGatewaySettings.get_settings(link.hub_id)

    return render(request, 'online_payments/pages/checkout.html', {
        'link': link,
        'gateway_settings': settings,
    })


# ============================================================================
# API - Create Payment Session
# ============================================================================

@require_http_methods(["POST"])
@login_required
def api_create_session(request):
    """Create a payment session with the configured gateway."""
    hub = _hub_id(request)

    try:
        body = json.loads(request.body)
        amount = Decimal(str(body.get('amount', 0)))
        currency = body.get('currency', 'EUR')
        description = body.get('description', '')
        customer_email = body.get('customer_email', '')
        customer_name = body.get('customer_name', '')
        source_type = body.get('source_type', '')
        source_id = body.get('source_id')
        payment_link_slug = body.get('payment_link_slug', '')

        if amount <= 0:
            return JsonResponse({
                'success': False,
                'error': str(_('Amount must be greater than zero.')),
            }, status=400)

        settings = PaymentGatewaySettings.get_settings(hub)

        if settings.active_gateway == 'none':
            return JsonResponse({
                'success': False,
                'error': str(_('No payment gateway configured.')),
            }, status=400)

        # Create transaction record
        transaction = PaymentTransaction.objects.create(
            hub_id=hub,
            gateway=settings.active_gateway,
            amount=amount,
            currency=currency,
            status='pending',
            customer_email=customer_email,
            customer_name=customer_name,
            description=description,
            source_type=source_type,
            source_id=source_id,
            metadata={
                'payment_link_slug': payment_link_slug,
            },
        )

        # Gateway-specific session creation
        session_data = {
            'transaction_id': transaction.transaction_id,
            'gateway': settings.active_gateway,
        }

        if settings.active_gateway == 'stripe':
            session_data['stripe_public_key'] = settings.stripe_public_key
            # In production, create a Stripe Checkout Session here
            # For now, return the transaction reference
            session_data['message'] = str(
                _('Stripe session created. Integrate Stripe.js for checkout.')
            )

        elif settings.active_gateway == 'redsys':
            session_data['redsys_environment'] = settings.redsys_environment
            # In production, generate Redsys form parameters here
            session_data['message'] = str(
                _('Redsys session created. Redirect to Redsys payment form.')
            )

        elif settings.active_gateway == 'manual':
            transaction.status = 'processing'
            transaction.save(update_fields=['status', 'updated_at'])
            session_data['message'] = str(
                _('Manual payment pending confirmation.')
            )

        return JsonResponse({
            'success': True,
            **session_data,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# API - Webhook Handler
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_webhook(request):
    """
    Webhook handler for payment gateway notifications.
    No login required. CSRF exempt.
    """
    try:
        body = json.loads(request.body)
        gateway = body.get('gateway', '')

        if gateway == 'stripe':
            return _handle_stripe_webhook(request, body)
        elif gateway == 'redsys':
            return _handle_redsys_webhook(request, body)
        else:
            return JsonResponse({'error': 'Unknown gateway'}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def _handle_stripe_webhook(request, body):
    """Handle Stripe webhook events."""
    event_type = body.get('type', '')
    data = body.get('data', {}).get('object', {})

    transaction_id = data.get('metadata', {}).get('transaction_id', '')
    if not transaction_id:
        return JsonResponse({'error': 'Missing transaction_id'}, status=400)

    try:
        transaction = PaymentTransaction.all_objects.get(
            transaction_id=transaction_id,
        )
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)

    if event_type == 'checkout.session.completed':
        transaction.gateway_reference = data.get('payment_intent', '')
        transaction.payment_method_type = data.get('payment_method_types', ['card'])[0]
        transaction.mark_completed()

        # Increment payment link usage if applicable
        slug = transaction.metadata.get('payment_link_slug')
        if slug:
            try:
                link = PaymentLink.objects.get(slug=slug)
                link.current_uses += 1
                link.save(update_fields=['current_uses', 'updated_at'])
            except PaymentLink.DoesNotExist:
                pass

    elif event_type == 'checkout.session.expired':
        transaction.mark_failed('Session expired')

    elif event_type == 'charge.refunded':
        refund_amount = Decimal(str(data.get('amount_refunded', 0))) / 100
        if refund_amount > 0:
            transaction.process_refund(refund_amount)

    return JsonResponse({'received': True})


def _handle_redsys_webhook(request, body):
    """Handle Redsys notification."""
    transaction_id = body.get('Ds_Order', '')
    response_code = body.get('Ds_Response', '')

    if not transaction_id:
        return JsonResponse({'error': 'Missing Ds_Order'}, status=400)

    try:
        transaction = PaymentTransaction.all_objects.get(
            transaction_id=transaction_id,
        )
    except PaymentTransaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)

    # Redsys response codes: 0000-0099 = approved
    try:
        code = int(response_code)
        if 0 <= code <= 99:
            transaction.gateway_reference = body.get('Ds_AuthorisationCode', '')
            transaction.mark_completed()

            # Increment payment link usage
            slug = transaction.metadata.get('payment_link_slug')
            if slug:
                try:
                    link = PaymentLink.objects.get(slug=slug)
                    link.current_uses += 1
                    link.save(update_fields=['current_uses', 'updated_at'])
                except PaymentLink.DoesNotExist:
                    pass
        else:
            transaction.mark_failed(f'Redsys error code: {response_code}')
    except (ValueError, TypeError):
        transaction.mark_failed(f'Invalid Redsys response: {response_code}')

    return JsonResponse({'received': True})


# ============================================================================
# Settings
# ============================================================================

@require_http_methods(["GET"])
@login_required
@with_module_nav('online_payments', 'settings')
@htmx_view(
    'online_payments/pages/settings.html',
    'online_payments/partials/settings_content.html',
)
def settings_view(request):
    hub = _hub_id(request)
    settings = PaymentGatewaySettings.get_settings(hub)
    form = PaymentGatewaySettingsForm(instance=settings)

    return {
        'config': settings,
        'settings_form': form,
    }


@require_http_methods(["POST"])
@login_required
def settings_save(request):
    """Save payment gateway settings."""
    hub = _hub_id(request)

    try:
        settings = PaymentGatewaySettings.get_settings(hub)

        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        # Update fields
        settings.active_gateway = data.get('active_gateway', settings.active_gateway)

        # Stripe
        stripe_public = data.get('stripe_public_key')
        if stripe_public is not None:
            settings.stripe_public_key = stripe_public
        stripe_secret = data.get('stripe_secret_key')
        if stripe_secret is not None and stripe_secret != '':
            settings.stripe_secret_key = stripe_secret
        stripe_webhook = data.get('stripe_webhook_secret')
        if stripe_webhook is not None and stripe_webhook != '':
            settings.stripe_webhook_secret = stripe_webhook

        # Redsys
        redsys_merchant = data.get('redsys_merchant_code')
        if redsys_merchant is not None:
            settings.redsys_merchant_code = redsys_merchant
        redsys_secret = data.get('redsys_secret_key')
        if redsys_secret is not None and redsys_secret != '':
            settings.redsys_secret_key = redsys_secret
        redsys_terminal = data.get('redsys_terminal')
        if redsys_terminal is not None:
            settings.redsys_terminal = redsys_terminal
        redsys_env = data.get('redsys_environment')
        if redsys_env is not None:
            settings.redsys_environment = redsys_env

        # General
        currency = data.get('currency')
        if currency is not None:
            settings.currency = currency

        require_deposit = data.get('require_deposit')
        if require_deposit is not None:
            settings.require_deposit = require_deposit in (True, 'true', 'on', '1')

        deposit_pct = data.get('deposit_percentage')
        if deposit_pct is not None:
            settings.deposit_percentage = Decimal(str(deposit_pct))

        # URLs
        success_url = data.get('success_url')
        if success_url is not None:
            settings.success_url = success_url
        cancel_url = data.get('cancel_url')
        if cancel_url is not None:
            settings.cancel_url = cancel_url

        # Notifications
        notification_email = data.get('notification_email')
        if notification_email is not None:
            settings.notification_email = notification_email

        settings.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
