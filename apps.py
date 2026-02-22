from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OnlinePaymentsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'online_payments'
    label = 'online_payments'
    verbose_name = _('Online Payments')

    def ready(self):
        pass
