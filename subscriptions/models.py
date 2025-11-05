# ============================================================================
# 3. APP: subscriptions
# ============================================================================
from django.db import models
from django.utils import timezone
from accounts.models import User

class SubscriptionPlan(models.Model):
    """Plans d'abonnement"""
    name = models.CharField(max_length=100)
    duration_months = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_listings = models.IntegerField()  # -1 = illimité
    is_premium = models.BooleanField(default=False)
    has_priority_support = models.BooleanField(default=False)
    has_featured_listings = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.duration_months} mois"


class Subscription(models.Model):
    """Abonnements des propriétaires"""
    STATUS_CHOICES = (
        ('trial', 'Essai gratuit'),
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_trial = models.BooleanField(default=False)
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def is_active(self):
        return self.status == 'active' and timezone.now() < self.end_date




class Payment(models.Model):
    """Modèle de paiement"""
    
    PAYMENT_METHOD_CHOICES = (
        ('paydunya', 'PayDunya'),  # Méthode unique pour PayDunya
        # PayDunya supporte: MTN Mobile Money, Moov Money, Orange Money, Cartes bancaires
    )
    
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    )
    
    subscription = models.ForeignKey(
        'Subscription',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_provider_response = models.JSONField(
        blank=True,
        null=True,
        help_text="Réponse complète de PayDunya"
    )
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"
    
    @property
    def is_completed(self):
        """Vérifie si le paiement est complété"""
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        """Vérifie si le paiement est en attente"""
        return self.status == 'pending'
    
    @property
    def paydunya_token(self):
        """Récupère le token PayDunya de la réponse"""
        if self.payment_provider_response:
            return self.payment_provider_response.get('token')
        return None
    
    @property
    def paydunya_receipt_url(self):
        """Récupère l'URL du reçu PayDunya"""
        if self.payment_provider_response:
            return self.payment_provider_response.get('receipt_url')
        return None




