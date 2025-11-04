from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AvailabilityRequestViewSet,
    ContactMessageViewSet,
    ReviewViewSet,
    FavoriteViewSet
)

# Configuration du router
router = DefaultRouter()
router.register(r'availability-requests', AvailabilityRequestViewSet, basename='availabilityrequest')
router.register(r'contact-messages', ContactMessageViewSet, basename='contactmessage')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

app_name = 'interactions'

urlpatterns = [
    # Routes du router
    path('', include(router.urls)),
]