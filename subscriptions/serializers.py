from rest_framework import serializers
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import SubscriptionPlan, Subscription, Payment
from accounts.models import User


# ============================================================================
# SubscriptionPlan Serializers
# ============================================================================

class SubscriptionPlanListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des plans d'abonnement"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'duration_months', 'price', 'max_listings',
            'is_premium', 'has_priority_support', 'has_featured_listings',
            'description', 'is_active'
        ]
        read_only_fields = ['id']


class SubscriptionPlanDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un plan d'abonnement"""
    features = serializers.SerializerMethodField()
    price_per_month = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'duration_months', 'price', 'price_per_month',
            'max_listings', 'is_premium', 'has_priority_support',
            'has_featured_listings', 'description', 'is_active', 'features'
        ]
        read_only_fields = ['id']
    
    def get_features(self, obj):
        """Liste des fonctionnalités du plan"""
        features = []
        
        if obj.max_listings == -1:
            features.append("Annonces illimitées")
        else:
            features.append(f"Jusqu'à {obj.max_listings} annonces")
        
        if obj.is_premium:
            features.append("Accès Premium")
        
        if obj.has_priority_support:
            features.append("Support prioritaire")
        
        if obj.has_featured_listings:
            features.append("Mise en avant des annonces")
        
        features.append(f"Durée: {obj.duration_months} mois")
        
        return features
    
    def get_price_per_month(self, obj):
        """Prix par mois"""
        if obj.duration_months > 0:
            return round(float(obj.price) / obj.duration_months, 2)
        return 0


class SubscriptionPlanCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/modifier un plan (Admin uniquement)"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'name', 'duration_months', 'price', 'max_listings',
            'is_premium', 'has_priority_support', 'has_featured_listings',
            'description', 'is_active'
        ]
    
    def validate_duration_months(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "La durée doit être supérieure à 0 mois."
            )
        return value
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Le prix ne peut pas être négatif."
            )
        return value
    
    def validate_max_listings(self, value):
        if value < -1:
            raise serializers.ValidationError(
                "Le nombre maximum d'annonces doit être -1 (illimité) ou positif."
            )
        return value


# ============================================================================
# Subscription Serializers
# ============================================================================

class SubscriptionListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des abonnements"""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_currently_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_name', 'plan', 'plan_name', 'status',
            'start_date', 'end_date', 'is_trial', 'auto_renew',
            'days_remaining', 'is_currently_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_days_remaining(self, obj):
        """Jours restants avant expiration"""
        if obj.status in ['expired', 'cancelled']:
            return 0
        
        remaining = (obj.end_date - timezone.now()).days
        return max(0, remaining)
    
    def get_is_currently_active(self, obj):
        """Vérifier si l'abonnement est actuellement actif"""
        return obj.is_active()


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un abonnement"""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_details = SubscriptionPlanListSerializer(source='plan', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_currently_active = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_name', 'user_email', 'plan', 'plan_name',
            'plan_details', 'status', 'start_date', 'end_date', 'is_trial',
            'auto_renew', 'days_remaining', 'is_currently_active',
            'total_paid', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_days_remaining(self, obj):
        if obj.status in ['expired', 'cancelled']:
            return 0
        remaining = (obj.end_date - timezone.now()).days
        return max(0, remaining)
    
    def get_is_currently_active(self, obj):
        return obj.is_active()
    
    def get_total_paid(self, obj):
        """Total payé pour cet abonnement"""
        total = obj.payments.filter(status='completed').aggregate(
            models.Sum('amount')
        )['amount__sum']
        return float(total) if total else 0.0


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un abonnement"""
    
    class Meta:
        model = Subscription
        fields = ['plan', 'auto_renew']
    
    def validate_plan(self, value):
        """Vérifier que le plan est actif"""
        if not value.is_active:
            raise serializers.ValidationError(
                "Ce plan d'abonnement n'est plus disponible."
            )
        return value
    
    def validate(self, data):
        """Vérifier qu'un utilisateur n'a qu'un seul abonnement actif"""
        request = self.context.get('request')
        
        if request:
            # Vérifier si l'utilisateur a déjà un abonnement actif
            active_subscription = Subscription.objects.filter(
                user=request.user,
                status__in=['trial', 'active'],
                end_date__gt=timezone.now()
            ).exists()
            
            if active_subscription:
                raise serializers.ValidationError(
                    "Vous avez déjà un abonnement actif. Veuillez attendre son expiration ou l'annuler."
                )
        
        return data
    
    def create(self, validated_data):
        """Créer l'abonnement avec dates calculées"""
        user = self.context['request'].user
        plan = validated_data['plan']
        
        # Vérifier si c'est le premier abonnement (essai gratuit)
        has_previous_subscription = Subscription.objects.filter(user=user).exists()
        
        start_date = timezone.now()
        
        if not has_previous_subscription:
            # Premier abonnement = 1 mois d'essai gratuit
            end_date = start_date + relativedelta(months=1)
            is_trial = True
            status = 'trial'
        else:
            # Abonnements suivants = durée du plan
            end_date = start_date + relativedelta(months=plan.duration_months)
            is_trial = False
            status = 'pending'  # En attente de paiement
        
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status=status,
            start_date=start_date,
            end_date=end_date,
            is_trial=is_trial,
            auto_renew=validated_data.get('auto_renew', False)
        )
        
        return subscription


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour un abonnement"""
    
    class Meta:
        model = Subscription
        fields = ['auto_renew', 'status']
    
    def validate_status(self, value):
        """Seuls certains changements de statut sont autorisés"""
        allowed_transitions = {
            'trial': ['active', 'expired', 'cancelled'],
            'active': ['expired', 'cancelled'],
            'expired': [],
            'cancelled': []
        }
        
        current_status = self.instance.status
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Impossible de passer de {current_status} à {value}."
            )
        
        return value


# ============================================================================
# Payment Serializers
# ============================================================================

class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des paiements"""
    subscription_plan = serializers.CharField(source='subscription.plan.name', read_only=True)
    user_name = serializers.CharField(source='subscription.user.get_full_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'subscription', 'subscription_plan', 'user_name',
            'amount', 'payment_method', 'status', 'transaction_id',
            'paid_at', 'created_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at']


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un paiement"""
    subscription_plan = serializers.CharField(source='subscription.plan.name', read_only=True)
    user_name = serializers.CharField(source='subscription.user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='subscription.user.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'subscription', 'subscription_plan', 'user_name',
            'user_email', 'amount', 'payment_method', 'status',
            'transaction_id', 'payment_provider_response',
            'paid_at', 'created_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at']


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer pour initier un paiement"""
    subscription = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.all()
    )
    payment_method = serializers.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES
    )
    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        help_text="Requis pour Mobile Money"
    )
    
    def validate_subscription(self, value):
        """Vérifier que l'abonnement appartient à l'utilisateur"""
        request = self.context.get('request')
        if request and value.user != request.user:
            raise serializers.ValidationError(
                "Cet abonnement ne vous appartient pas."
            )
        
        # Vérifier que l'abonnement n'est pas déjà payé
        if value.is_trial:
            raise serializers.ValidationError(
                "L'essai gratuit ne nécessite pas de paiement."
            )
        
        if value.status == 'active':
            raise serializers.ValidationError(
                "Cet abonnement est déjà actif."
            )
        
        return value
    
    def validate(self, data):
        """Validations croisées"""
        payment_method = data.get('payment_method')
        phone_number = data.get('phone_number')
        
        # Vérifier que le numéro de téléphone est fourni pour Mobile Money
        if payment_method in ['mtn_momo', 'moov_money'] and not phone_number:
            raise serializers.ValidationError({
                'phone_number': "Le numéro de téléphone est requis pour Mobile Money."
            })
        
        return data


class PaymentCallbackSerializer(serializers.Serializer):
    """Serializer pour le callback des prestataires de paiement"""
    transaction_id = serializers.CharField()
    status = serializers.ChoiceField(choices=['success', 'failed'])
    provider_response = serializers.JSONField(required=False)


class PaymentStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mise à jour du statut de paiement (Admin)"""
    
    class Meta:
        model = Payment
        fields = ['status', 'payment_provider_response', 'paid_at']
    
    def validate_status(self, value):
        """Vérifier les transitions de statut autorisées"""
        allowed_transitions = {
            'pending': ['completed', 'failed'],
            'completed': ['refunded'],
            'failed': [],
            'refunded': []
        }
        
        current_status = self.instance.status
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Impossible de passer de {current_status} à {value}."
            )
        
        return value
    
    def validate(self, data):
        """Ajouter la date de paiement si complété"""
        if data.get('status') == 'completed' and not data.get('paid_at'):
            data['paid_at'] = timezone.now()
        
        return data


# ============================================================================
# Statistics Serializers
# ============================================================================

class SubscriptionStatsSerializer(serializers.Serializer):
    """Statistiques des abonnements"""
    total_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    trial_subscriptions = serializers.IntegerField()
    expired_subscriptions = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    conversion_rate = serializers.FloatField()


class UserSubscriptionStatusSerializer(serializers.Serializer):
    """Statut d'abonnement d'un utilisateur"""
    has_active_subscription = serializers.BooleanField()
    current_subscription = SubscriptionDetailSerializer(allow_null=True)
    can_create_listings = serializers.BooleanField()
    remaining_listings = serializers.IntegerField()
    days_remaining = serializers.IntegerField()