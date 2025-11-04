# ============================================================================
# 5. APP: core
# ============================================================================
from django.db import models
from accounts.models import User

class StaticPage(models.Model):
    """Pages statiques (CGU, FAQ, etc.)"""
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    meta_description = models.TextField(blank=True, null=True)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


class Notification(models.Model):
    """Notifications utilisateurs"""
    TYPE_CHOICES = (
        ('subscription_expiring', 'Abonnement expire bientôt'),
        ('listing_approved', 'Annonce approuvée'),
        ('listing_rejected', 'Annonce rejetée'),
        ('new_message', 'Nouveau message'),
        ('new_review', 'Nouvel avis'),
        ('new_availability_request', 'Nouvelle demande disponibilité'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']


class Analytics(models.Model):
    """Statistiques globales"""
    date = models.DateField(unique=True)
    new_users = models.IntegerField(default=0)
    new_listings = models.IntegerField(default=0)
    active_subscriptions = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_searches = models.IntegerField(default=0)
    total_contacts = models.IntegerField(default=0)


