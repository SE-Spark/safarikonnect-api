from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, DriverViewSet, BusinessViewSet, BidViewSet,
    VehicleColorViewSet, VehicleTypeViewSet,
    VehicleMakeViewSet, VehicleModelViewSet,
    WalletViewSet, TransactionalWalletViewSet, PaymentTransactionViewSet,
    FeedbackViewSet, GeofenceViewSet, StatisticsViewSet,AuthViewSet, RideViewSet,
    TicketViewSet, TicketCategoryViewSet, payment_webhook
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'businesses', BusinessViewSet, basename='business')
router.register(r'bids', BidViewSet, basename='bid')
router.register(r'vehicle-colors', VehicleColorViewSet)
router.register(r'vehicle-types', VehicleTypeViewSet)
router.register(r'vehicle-makes', VehicleMakeViewSet)
router.register(r'vehicle-models', VehicleModelViewSet)
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionalWalletViewSet, basename='transaction')
router.register(r'payments', PaymentTransactionViewSet, basename='payment')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'geofences', GeofenceViewSet)
router.register(r'statistics', StatisticsViewSet, basename='statistics')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'rides', RideViewSet, basename='ride')
router.register(r'ticket-categories', TicketCategoryViewSet, basename='ticket-category')
router.register(r'tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    path('', include(router.urls)),
    path('payment-webhook/', payment_webhook, name='payment-webhook'),
]