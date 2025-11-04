# core/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import StaticPage, Notification, Analytics
from .serializers import (
    StaticPageSerializer, StaticPageListSerializer,
    NotificationSerializer, NotificationMarkReadSerializer,
    AnalyticsSerializer, AnalyticsSummarySerializer,
    DashboardStatsSerializer
)
from accounts.models import User
from listings.models import PropertyGroup, Listing
from subscriptions.models import Subscription, Payment
from interactions.models import Review, AvailabilityRequest


class StaticPageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des pages statiques (CGU, FAQ, Politique de confidentialité)
    - List/Retrieve: Public
    - Create/Update/Delete: Admin seulement (EF-A-07)
    """
    queryset = StaticPage.objects.all()
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StaticPageListSerializer
        return StaticPageSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        queryset = StaticPage.objects.all()
        # Filtrer les pages non publiées pour les non-admins
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        return queryset


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les notifications utilisateurs
    - List: Toutes les notifications de l'utilisateur
    - Retrieve: Détail d'une notification
    - Mark as read: Action pour marquer comme lu
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Retourne le nombre de notifications non lues"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def mark_multiple_read(self, request):
        """Marquer plusieurs notifications comme lues"""
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        
        if serializer.validated_data.get('mark_all'):
            # Marquer toutes les notifications comme lues
            updated = queryset.filter(is_read=False).update(is_read=True)
            return Response({
                'message': f'{updated} notification(s) marquée(s) comme lue(s)',
                'updated_count': updated
            })
        
        # Marquer les notifications spécifiées
        notification_ids = serializer.validated_data.get('notification_ids', [])
        updated = queryset.filter(
            id__in=notification_ids,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'message': f'{updated} notification(s) marquée(s) comme lue(s)',
            'updated_count': updated
        })
    
    @action(detail=False, methods=['delete'])
    def delete_all_read(self, request):
        """Supprimer toutes les notifications lues"""
        deleted_count, _ = self.get_queryset().filter(is_read=True).delete()
        return Response({
            'message': f'{deleted_count} notification(s) supprimée(s)',
            'deleted_count': deleted_count
        })


class AnalyticsViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les statistiques globales (EF-A-08)
    Accessible uniquement aux administrateurs
    """
    queryset = Analytics.objects.all().order_by('-date')
    serializer_class = AnalyticsSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Résumé des statistiques sur une période donnée
        Query params: start_date, end_date (format: YYYY-MM-DD)
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Par défaut: 30 derniers jours
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        
        # Récupérer les données
        analytics = Analytics.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Calculer les totaux
        aggregates = analytics.aggregate(
            total_users=Sum('new_users'),
            total_listings=Sum('new_listings'),
            total_active_subscriptions=Sum('active_subscriptions'),
            total_revenue=Sum('revenue'),
            total_searches=Sum('total_searches'),
            total_contacts=Sum('total_contacts')
        )
        
        summary_data = {
            'total_users': aggregates['total_users'] or 0,
            'total_listings': aggregates['total_listings'] or 0,
            'total_active_subscriptions': aggregates['total_active_subscriptions'] or 0,
            'total_revenue': aggregates['total_revenue'] or 0,
            'total_searches': aggregates['total_searches'] or 0,
            'total_contacts': aggregates['total_contacts'] or 0,
            'period_start': start_date,
            'period_end': end_date,
            'daily_breakdown': analytics
        }
        
        serializer = AnalyticsSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Statistiques complètes pour le tableau de bord admin (EF-A-08)
        """
        today = timezone.now().date()
        first_day_month = today.replace(day=1)
        first_day_year = today.replace(month=1, day=1)
        
        # Statistiques utilisateurs
        total_users = User.objects.count()
        total_proprietaires = User.objects.filter(user_type='proprietaire').count()
        total_locataires = User.objects.filter(user_type='locataire').count()
        
        # Statistiques annonces
        total_listings = Listing.objects.count()
        published_listings = Listing.objects.filter(status='published').count()
        pending_listings = Listing.objects.filter(status='pending').count()
        
        # Statistiques groupes de propriétés
        total_property_groups = PropertyGroup.objects.count()
        
        # Statistiques abonnements
        active_subscriptions = Subscription.objects.filter(
            status='active',
            end_date__gte=timezone.now()
        ).count()
        
        expired_subscriptions = Subscription.objects.filter(
            status='expired'
        ).count()
        
        trial_subscriptions = Subscription.objects.filter(
            status='trial',
            is_trial=True
        ).count()
        
        # Revenus (basés sur les paiements complétés)
        revenue_today = Payment.objects.filter(
            status='completed',
            paid_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        revenue_month = Payment.objects.filter(
            status='completed',
            paid_at__date__gte=first_day_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        revenue_year = Payment.objects.filter(
            status='completed',
            paid_at__date__gte=first_day_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Vérifications d'identité en attente (EF-A-02)
        pending_verifications = User.objects.filter(
            user_type='proprietaire',
            is_identity_verified=False,
            identity_document__isnull=False
        ).count()
        
        # Statistiques avis (EF-A-04)
        total_reviews = Review.objects.count()
        pending_reviews = Review.objects.filter(status='pending').count()
        
        # Demandes de disponibilité
        total_availability_requests = AvailabilityRequest.objects.count()
        pending_availability_requests = AvailabilityRequest.objects.filter(
            status='pending'
        ).count()
        
        stats_data = {
            'total_users': total_users,
            'total_proprietaires': total_proprietaires,
            'total_locataires': total_locataires,
            'total_listings': total_listings,
            'published_listings': published_listings,
            'pending_listings': pending_listings,
            'total_property_groups': total_property_groups,
            'active_subscriptions': active_subscriptions,
            'expired_subscriptions': expired_subscriptions,
            'trial_subscriptions': trial_subscriptions,
            'total_revenue_today': revenue_today,
            'total_revenue_month': revenue_month,
            'total_revenue_year': revenue_year,
            'pending_identity_verifications': pending_verifications,
            'total_reviews': total_reviews,
            'pending_reviews': pending_reviews,
            'total_availability_requests': total_availability_requests,
            'pending_availability_requests': pending_availability_requests,
        }
        
        serializer = DashboardStatsSerializer(stats_data)
        return Response(serializer.data)