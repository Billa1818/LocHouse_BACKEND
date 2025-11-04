# core/serializers.py
from rest_framework import serializers
from .models import StaticPage, Notification, Analytics


class StaticPageSerializer(serializers.ModelSerializer):
    """Serializer pour les pages statiques (CGU, FAQ, etc.)"""
    
    class Meta:
        model = StaticPage
        fields = [
            'id', 'slug', 'title', 'content', 
            'meta_description', 'is_published', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class StaticPageListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des pages statiques"""
    
    class Meta:
        model = StaticPage
        fields = ['id', 'slug', 'title', 'meta_description', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications utilisateurs"""
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'title', 'message', 'link', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'notification_type_display']


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer pour marquer une ou plusieurs notifications comme lues"""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Liste des IDs de notifications à marquer comme lues"
    )
    mark_all = serializers.BooleanField(
        default=False,
        help_text="Marquer toutes les notifications comme lues"
    )
    
    def validate(self, data):
        if not data.get('mark_all') and not data.get('notification_ids'):
            raise serializers.ValidationError(
                "Vous devez fournir 'notification_ids' ou 'mark_all=true'"
            )
        return data


class AnalyticsSerializer(serializers.ModelSerializer):
    """Serializer pour les statistiques globales"""
    
    class Meta:
        model = Analytics
        fields = [
            'id', 'date', 'new_users', 'new_listings',
            'active_subscriptions', 'revenue', 'total_searches', 'total_contacts'
        ]
        read_only_fields = ['id']


class AnalyticsSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des statistiques sur une période"""
    
    total_users = serializers.IntegerField()
    total_listings = serializers.IntegerField()
    total_active_subscriptions = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_searches = serializers.IntegerField()
    total_contacts = serializers.IntegerField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    daily_breakdown = AnalyticsSerializer(many=True, read_only=True)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du tableau de bord admin"""
    
    total_users = serializers.IntegerField()
    total_proprietaires = serializers.IntegerField()
    total_locataires = serializers.IntegerField()
    total_listings = serializers.IntegerField()
    published_listings = serializers.IntegerField()
    pending_listings = serializers.IntegerField()
    total_property_groups = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    expired_subscriptions = serializers.IntegerField()
    trial_subscriptions = serializers.IntegerField()
    total_revenue_today = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_revenue_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_revenue_year = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_identity_verifications = serializers.IntegerField()
    total_reviews = serializers.IntegerField()
    pending_reviews = serializers.IntegerField()
    total_availability_requests = serializers.IntegerField()
    pending_availability_requests = serializers.IntegerField()