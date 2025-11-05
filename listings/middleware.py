# listings/middleware.py
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import Subscription
from listings.models import PropertyGroup


class PropertyGroupLimitMiddleware:
    """
    Middleware pour limiter la création de PropertyGroup pendant l'essai gratuit
    et gérer la suppression après expiration.
    
    Règles:
    - Sans abonnement: maximum 5 PropertyGroup pendant 1 mois d'essai
    - Après 1 mois sans abonnement: suppression de tous les PropertyGroup
    - Avec abonnement actif: création illimitée
    - Abonnement expiré: suppression de tous les PropertyGroup
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.FREE_TRIAL_DAYS = 30
        self.MAX_FREE_PROPERTY_GROUPS = 5
        self.TARGET_PATH = '/api/listings/property-groups/'
    
    def __call__(self, request):
        # Vérifier uniquement pour POST sur l'endpoint de création
        if request.path == self.TARGET_PATH and request.method == 'POST':
            # Vérifier que l'utilisateur est authentifié et propriétaire
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentification requise'
                }, status=401)
            
            if request.user.user_type != 'proprietaire':
                return JsonResponse({
                    'error': 'Seuls les propriétaires peuvent créer des groupes de propriétés'
                }, status=403)
            
            # Vérifier le statut d'abonnement
            validation_result = self._validate_property_group_creation(request.user)
            
            if not validation_result['allowed']:
                return JsonResponse({
                    'error': validation_result['message'],
                    'detail': validation_result.get('detail', {}),
                    'upgrade_required': validation_result.get('upgrade_required', False)
                }, status=403)
        
        # Continuer le traitement normal
        response = self.get_response(request)
        return response
    
    def _validate_property_group_creation(self, user):
        """
        Valide si l'utilisateur peut créer un nouveau PropertyGroup
        
        Returns:
            dict: {
                'allowed': bool,
                'message': str,
                'detail': dict (optional),
                'upgrade_required': bool (optional)
            }
        """
        # Récupérer l'abonnement actif
        active_subscription = Subscription.objects.filter(
            user=user,
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        if active_subscription:
            # Utilisateur avec abonnement actif : création illimitée
            return {
                'allowed': True,
                'message': 'Création autorisée'
            }
        
        # Pas d'abonnement actif : vérifier l'essai gratuit
        return self._check_free_trial_limits(user)
    
    def _check_free_trial_limits(self, user):
        """
        Vérifie les limitations de l'essai gratuit
        """
        # Calculer la date de fin de l'essai gratuit (30 jours après inscription)
        trial_end_date = user.created_at + timedelta(days=self.FREE_TRIAL_DAYS)
        current_date = timezone.now()
        
        # Vérifier si l'essai gratuit est expiré
        if current_date > trial_end_date:
            # Essai expiré : supprimer tous les PropertyGroup existants
            self._delete_user_property_groups(user)
            
            return {
                'allowed': False,
                'message': 'Votre période d\'essai gratuit de 30 jours est expirée',
                'detail': {
                    'trial_started': user.created_at.isoformat(),
                    'trial_ended': trial_end_date.isoformat(),
                    'days_since_expiry': (current_date - trial_end_date).days
                },
                'upgrade_required': True
            }
        
        # Essai gratuit actif : vérifier la limite de 5 PropertyGroup
        current_count = PropertyGroup.objects.filter(owner=user).count()
        
        if current_count >= self.MAX_FREE_PROPERTY_GROUPS:
            days_remaining = (trial_end_date - current_date).days
            
            return {
                'allowed': False,
                'message': f'Limite atteinte : {self.MAX_FREE_PROPERTY_GROUPS} groupes maximum pendant l\'essai gratuit',
                'detail': {
                    'current_count': current_count,
                    'max_allowed': self.MAX_FREE_PROPERTY_GROUPS,
                    'trial_days_remaining': days_remaining,
                    'trial_end_date': trial_end_date.isoformat()
                },
                'upgrade_required': True
            }
        
        # Encore dans la limite
        days_remaining = (trial_end_date - current_date).days
        
        return {
            'allowed': True,
            'message': 'Création autorisée',
            'detail': {
                'current_count': current_count,
                'max_allowed': self.MAX_FREE_PROPERTY_GROUPS,
                'remaining_slots': self.MAX_FREE_PROPERTY_GROUPS - current_count,
                'trial_days_remaining': days_remaining
            }
        }
    
    def _delete_user_property_groups(self, user):
        """
        Supprime tous les PropertyGroup de l'utilisateur
        (appelé quand l'essai ou l'abonnement expire)
        """
        deleted_count, _ = PropertyGroup.objects.filter(owner=user).delete()
        
        if deleted_count > 0:
            print(f"[PropertyGroupLimitMiddleware] Supprimé {deleted_count} PropertyGroup pour l'utilisateur {user.id} (essai/abonnement expiré)")
        
        return deleted_count