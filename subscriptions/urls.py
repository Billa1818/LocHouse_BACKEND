from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet,
    SubscriptionViewSet,
    PaymentViewSet,
    SubscriptionAdminViewSet
)

# Configuration du router
router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='subscriptionplan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'admin', SubscriptionAdminViewSet, basename='subscription-admin')

app_name = 'subscriptions'

urlpatterns = [
    # Routes du router
    path('', include(router.urls)),
]
