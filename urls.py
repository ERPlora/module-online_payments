from django.urls import path
from . import views

app_name = 'online_payments'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Transactions
    path('transactions/', views.transactions, name='transactions'),
    path('transactions/<uuid:pk>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/<uuid:pk>/refund/', views.refund, name='refund'),

    # Payment Links
    path('links/', views.payment_links, name='payment_links'),
    path('links/create/', views.payment_link_create, name='payment_link_create'),
    path('links/<uuid:pk>/deactivate/', views.payment_link_deactivate, name='payment_link_deactivate'),
    path('links/<uuid:pk>/delete/', views.payment_link_delete, name='payment_link_delete'),

    # Checkout (public, no login required)
    path('checkout/<slug:slug>/', views.checkout, name='checkout'),

    # API
    path('api/create-session/', views.api_create_session, name='api_create_session'),
    path('api/webhook/', views.api_webhook, name='api_webhook'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
]
