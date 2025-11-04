from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyGroupViewSet, ListingViewSet, ListingAmenityViewSet

# Configuration du router
router = DefaultRouter()
router.register(r'property-groups', PropertyGroupViewSet, basename='propertygroup')
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'amenities', ListingAmenityViewSet, basename='amenity')

app_name = 'listings'

urlpatterns = [
    # Routes du router
    path('', include(router.urls)),
]