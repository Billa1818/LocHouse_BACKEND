# ============================================================================
# 4. APP: interactions
# ============================================================================
from django.db import models
from django.utils import timezone
from accounts.models import User
from listings.models import Listing

class AvailabilityRequest(models.Model):
    """Demandes de disponibilité (NOUVELLE FONCTIONNALITÉ)"""
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('contacted', 'Contacté'),
        ('closed', 'Clôturé'),
    )
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='availability_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availability_requests')
    requester_phone = models.CharField(max_length=20)  # Numéro du client
    message = models.TextField()
    check_in_date = models.DateField(blank=True, null=True)
    check_out_date = models.DateField(blank=True, null=True)
    guests_count = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    owner_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Demande pour {self.listing.title} par {self.requester.get_full_name()}"


class ContactMessage(models.Model):
    """Messages entre locataires et propriétaires"""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='contact_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    is_first_contact = models.BooleanField(default=False)  # Déclenche révélation contact
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']


class Review(models.Model):
    """Avis et commentaires"""
    STATUS_CHOICES = (
        ('pending', 'En attente de modération'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    )
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')))
    comment = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['listing', 'author']  # 1 avis par utilisateur par annonce


class Favorite(models.Model):
    """Annonces favorites des locataires"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'listing']

