# ============================================================================
# 2. APP: listings
# ============================================================================
from django.db import models
from accounts.models import User


class PropertyGroup(models.Model):
    """Groupe de propriétés appartenant à un propriétaire"""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_groups')
    name = models.CharField(max_length=200)  # Ex: "Hôtel Dallas", "Résidence Le Palmier"
    description = models.TextField(blank=True, null=True)
    notifications_enabled = models.BooleanField(default=True)  # Activer/désactiver les notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Groupe de propriétés"
        verbose_name_plural = "Groupes de propriétés"
    
    def __str__(self):
        return f"{self.name} - {self.owner.get_full_name()}"


class Listing(models.Model):
    """Annonce de location"""
    CATEGORY_CHOICES = (
        ('residentiel', 'Résidentiel'),
        ('touristique', 'Touristique'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Brouillon'),
        ('pending', 'En attente de validation'),
        ('published', 'Publié'),
        ('rejected', 'Rejeté'),
        ('archived', 'Archivé'),
    )
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    property_group = models.ForeignKey(
        PropertyGroup, 
        on_delete=models.SET_NULL, 
        related_name='listings',
        blank=True, 
        null=True
    )  # Groupe auquel appartient cette maison
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    property_name = models.CharField(max_length=200, blank=True, null=True)  # Nom de la maison/hôtel
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Prix
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Localisation
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    
    # Caractéristiques
    bedrooms = models.IntegerField(default=1)
    bathrooms = models.IntegerField(default=1)
    area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # m²
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Métadonnées
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def are_notifications_enabled(self):
        """Vérifie si les notifications sont activées pour cette maison"""
        if self.property_group:
            return self.property_group.notifications_enabled
        return True  # Par défaut, notifications activées si pas de groupe


class ListingAmenity(models.Model):
    """Équipements disponibles"""
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Nom icône
    
    def __str__(self):
        return self.name


class ListingAmenityRelation(models.Model):
    """Relation Many-to-Many entre annonces et équipements"""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='amenities')
    amenity = models.ForeignKey(ListingAmenity, on_delete=models.CASCADE)


class ListingMedia(models.Model):
    """Photos et vidéos des annonces"""
    MEDIA_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Vidéo'),
    )
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(upload_to='listings/')
    video_url = models.URLField(blank=True, null=True)  # Pour vidéos externes
    order = models.IntegerField(default=0)
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']