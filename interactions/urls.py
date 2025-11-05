# ============================================================================
# interactions/urls.py
# ============================================================================
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AvailabilityRequestViewSet,
    ContactMessageViewSet,
    ReviewViewSet,
    FavoriteViewSet
)

# Configuration du routeur
router = DefaultRouter()
router.register(r'availability-requests', AvailabilityRequestViewSet, basename='availability-request')
router.register(r'messages', ContactMessageViewSet, basename='message')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

app_name = 'interactions'

urlpatterns = [
    path('', include(router.urls)),
]

