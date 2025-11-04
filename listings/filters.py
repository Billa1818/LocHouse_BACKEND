import django_filters
from .models import Listing


class ListingFilter(django_filters.FilterSet):
    """Filtres avancés pour les annonces"""
    
    # Filtres de localisation
    city = django_filters.CharFilter(lookup_expr='icontains')
    district = django_filters.CharFilter(lookup_expr='icontains')
    
    # Filtres de catégorie et type
    category = django_filters.ChoiceFilter(choices=Listing.CATEGORY_CHOICES)
    
    # Filtres de prix
    min_daily_price = django_filters.NumberFilter(field_name='daily_price', lookup_expr='gte')
    max_daily_price = django_filters.NumberFilter(field_name='daily_price', lookup_expr='lte')
    min_monthly_price = django_filters.NumberFilter(field_name='monthly_price', lookup_expr='gte')
    max_monthly_price = django_filters.NumberFilter(field_name='monthly_price', lookup_expr='lte')
    
    # Filtres de caractéristiques
    min_bedrooms = django_filters.NumberFilter(field_name='bedrooms', lookup_expr='gte')
    max_bedrooms = django_filters.NumberFilter(field_name='bedrooms', lookup_expr='lte')
    min_bathrooms = django_filters.NumberFilter(field_name='bathrooms', lookup_expr='gte')
    min_area = django_filters.NumberFilter(field_name='area', lookup_expr='gte')
    
    # Filtre par statut (pour propriétaires et admins)
    status = django_filters.ChoiceFilter(choices=Listing.STATUS_CHOICES)
    
    # Filtre par groupe de propriétés
    property_group = django_filters.NumberFilter(field_name='property_group__id')
    
    # Filtre par propriétaire
    owner = django_filters.NumberFilter(field_name='owner__id')
    
    class Meta:
        model = Listing
        fields = [
            'city', 'district', 'category', 'status',
            'min_daily_price', 'max_daily_price',
            'min_monthly_price', 'max_monthly_price',
            'min_bedrooms', 'max_bedrooms', 'min_bathrooms',
            'min_area', 'property_group', 'owner'
        ]