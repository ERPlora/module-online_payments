from django.utils.translation import gettext_lazy as _

MODULE_ID = 'online_payments'
MODULE_NAME = _('Online Payments')
MODULE_VERSION = '1.0.0'
MODULE_ICON = 'card-outline'
MODULE_DESCRIPTION = _('Payment gateway integration for online and remote payments')
MODULE_AUTHOR = 'ERPlora'
MODULE_CATEGORY = 'sales'

MENU = {
    'label': _('Online Payments'),
    'icon': 'card-outline',
    'order': 40,
}

NAVIGATION = [
    {'label': _('Dashboard'), 'icon': 'speedometer-outline', 'id': 'dashboard'},
    {'label': _('Transactions'), 'icon': 'list-outline', 'id': 'transactions'},
    {'label': _('Payment Links'), 'icon': 'link-outline', 'id': 'payment_links'},
    {'label': _('Settings'), 'icon': 'settings-outline', 'id': 'settings'},
]

DEPENDENCIES = []

PERMISSIONS = [
    'online_payments.view_transaction',
    'online_payments.add_transaction',
    'online_payments.refund_transaction',
    'online_payments.view_payment_link',
    'online_payments.add_payment_link',
    'online_payments.delete_payment_link',
    'online_payments.manage_settings',
]
