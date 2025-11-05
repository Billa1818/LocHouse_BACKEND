from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import uuid
import requests
from django.conf import settings

from .models import SubscriptionPlan, Subscription, Payment
from listings.models import Listing
from core.models import Notification
from .serializers import (
    SubscriptionPlanListSerializer,
    SubscriptionPlanDetailSerializer,
    SubscriptionPlanCreateUpdateSerializer,
    SubscriptionListSerializer,
    SubscriptionDetailSerializer,
    SubscriptionCreateSerializer,
    SubscriptionUpdateSerializer,
    PaymentListSerializer,
    PaymentDetailSerializer,
    PaymentInitiateSerializer,
    PaymentCallbackSerializer,
    PaymentStatusUpdateSerializer,
    SubscriptionStatsSerializer,
    UserSubscriptionStatusSerializer
)
from .permissions import IsOwner, IsAdmin


# ============================================================================
# PayDunya Configuration
# ============================================================================

class PayDunyaService:
    """Service pour gérer les paiements via PayDunya"""
    
    def __init__(self):
        self.base_url = "https://app.paydunya.com/api/v1"
        self.master_key = settings.PAYDUNYA_MASTER_KEY
        self.private_key = settings.PAYDUNYA_PRIVATE_KEY
        self.token = settings.PAYDUNYA_TOKEN
        self.mode = getattr(settings, 'PAYDUNYA_MODE', 'test')
        
    def get_headers(self):
        """Headers pour les requêtes PayDunya"""
        return {
            'Content-Type': 'application/json',
            'PAYDUNYA-MASTER-KEY': self.master_key,
            'PAYDUNYA-PRIVATE-KEY': self.private_key,
            'PAYDUNYA-TOKEN': self.token
        }
    
    def create_invoice(self, payment, user, callback_url, return_url, cancel_url):
        """Créer une facture PayDunya"""
        
        invoice_data = {
            'invoice': {
                'total_amount': float(payment.amount),
                'description': f"Abonnement {payment.subscription.plan.name} - {payment.subscription.plan.duration_months} mois"
            },
            'store': {
                'name': getattr(settings, 'PAYDUNYA_STORE_NAME', 'LOMIMO'),
                'tagline': getattr(settings, 'PAYDUNYA_STORE_TAGLINE', 'Plateforme de location immobilière'),
                'website_url': getattr(settings, 'SITE_URL', 'https://lomimo.com')
            },
            'custom_data': {
                'payment_id': str(payment.id),
                'subscription_id': str(payment.subscription.id),
                'user_id': str(user.id)
            },
            'actions': {
                'callback_url': callback_url,
                'return_url': return_url,
                'cancel_url': cancel_url
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/checkout-invoice/create",
                json=invoice_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'token': data.get('token'),
                    'response_code': data.get('response_code'),
                    'response_text': data.get('response_text'),
                    'description': data.get('description'),
                    'invoice_url': data.get('response_text')  # URL de paiement
                }
            else:
                return {
                    'success': False,
                    'error': response.json()
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def confirm_invoice(self, token):
        """Confirmer le statut d'une facture PayDunya"""
        try:
            response = requests.get(
                f"{self.base_url}/checkout-invoice/confirm/{token}",
                headers=self.get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status'),
                    'response_code': data.get('response_code'),
                    'custom_data': data.get('custom_data'),
                    'receipt_url': data.get('receipt_url')
                }
            else:
                return {
                    'success': False,
                    'error': response.json()
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# Notification Helper
# ============================================================================

def create_notification(user, notification_type, title, message, link=None):
    """Créer une notification pour l'utilisateur"""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )


# ============================================================================
# SubscriptionPlan ViewSet
# ============================================================================

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les plans d'abonnement.
    - Public: voir les plans actifs
    - Admin: CRUD complet
    """
    queryset = SubscriptionPlan.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['duration_months', 'price']
    ordering = ['duration_months']
    
    def get_queryset(self):
        """Filtrer les plans selon le rôle"""
        if self.request.user.is_staff:
            return SubscriptionPlan.objects.all()
        return SubscriptionPlan.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SubscriptionPlanListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SubscriptionPlanCreateUpdateSerializer
        return SubscriptionPlanDetailSerializer
    
    def get_permissions(self):
        """Permissions selon l'action"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Plans recommandés selon le profil utilisateur"""
        plans = SubscriptionPlan.objects.filter(
            is_active=True
        ).annotate(
            subscription_count=Count('subscription')
        ).order_by('-subscription_count')[:3]
        
        serializer = SubscriptionPlanListSerializer(
            plans,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


# ============================================================================
# Subscription ViewSet
# ============================================================================

class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les abonnements.
    - Propriétaires: voir/créer leurs abonnements
    - Admin: gérer tous les abonnements
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_trial', 'plan']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les abonnements selon le rôle"""
        if self.request.user.is_staff:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SubscriptionListSerializer
        elif self.action == 'create':
            return SubscriptionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer
        return SubscriptionDetailSerializer
    
    def get_permissions(self):
        """Permissions selon l'action"""
        if self.action in ['create', 'list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated(), IsAdmin()]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Obtenir l'abonnement actif de l'utilisateur"""
        subscription = Subscription.objects.filter(
            user=request.user,
            status__in=['trial', 'active'],
            end_date__gt=timezone.now()
        ).first()
        
        if subscription:
            serializer = SubscriptionDetailSerializer(
                subscription,
                context={'request': request}
            )
            return Response(serializer.data)
        
        return Response({
            'message': 'Aucun abonnement actif',
            'has_subscription': False
        })
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Statut complet de l'abonnement utilisateur"""
        user = request.user
        
        subscription = Subscription.objects.filter(
            user=user,
            status__in=['trial', 'active'],
            end_date__gt=timezone.now()
        ).first()
        
        current_listings = Listing.objects.filter(owner=user).count()
        
        if subscription:
            max_listings = subscription.plan.max_listings
            can_create = (max_listings == -1) or (current_listings < max_listings)
            remaining_listings = -1 if max_listings == -1 else max(0, max_listings - current_listings)
            days_remaining = (subscription.end_date - timezone.now()).days
            
            data = {
                'has_active_subscription': True,
                'current_subscription': SubscriptionDetailSerializer(
                    subscription,
                    context={'request': request}
                ).data,
                'can_create_listings': can_create,
                'remaining_listings': remaining_listings,
                'days_remaining': days_remaining
            }
        else:
            data = {
                'has_active_subscription': False,
                'current_subscription': None,
                'can_create_listings': False,
                'remaining_listings': 0,
                'days_remaining': 0
            }
        
        serializer = UserSubscriptionStatusSerializer(data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annuler un abonnement"""
        subscription = self.get_object()
        
        if subscription.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à annuler cet abonnement'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if subscription.status in ['expired', 'cancelled']:
            return Response(
                {'error': 'Cet abonnement est déjà terminé'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.status = 'cancelled'
        subscription.auto_renew = False
        subscription.save()
        
        # Notification
        create_notification(
            user=subscription.user,
            notification_type='subscription_expiring',
            title='Abonnement annulé',
            message=f'Votre abonnement {subscription.plan.name} a été annulé.',
            link=f'/subscriptions/{subscription.id}'
        )
        
        return Response({
            'message': 'Abonnement annulé avec succès',
            'data': SubscriptionDetailSerializer(
                subscription,
                context={'request': request}
            ).data
        })
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renouveler un abonnement expiré"""
        old_subscription = self.get_object()
        
        if old_subscription.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à renouveler cet abonnement'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        active_subscription = Subscription.objects.filter(
            user=request.user,
            status__in=['trial', 'active'],
            end_date__gt=timezone.now()
        ).exists()
        
        if active_subscription:
            return Response(
                {'error': 'Vous avez déjà un abonnement actif'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_date = timezone.now()
        end_date = start_date + relativedelta(months=old_subscription.plan.duration_months)
        
        new_subscription = Subscription.objects.create(
            user=request.user,
            plan=old_subscription.plan,
            status='pending',
            start_date=start_date,
            end_date=end_date,
            is_trial=False,
            auto_renew=old_subscription.auto_renew
        )
        
        return Response({
            'message': 'Nouvel abonnement créé. Veuillez procéder au paiement.',
            'data': SubscriptionDetailSerializer(
                new_subscription,
                context={'request': request}
            ).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Historique des abonnements de l'utilisateur"""
        subscriptions = Subscription.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        serializer = SubscriptionListSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


# ============================================================================
# Payment ViewSet
# ============================================================================

class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les paiements avec PayDunya.
    - Utilisateurs: voir leurs paiements, initier des paiements
    - Admin: gérer tous les paiements
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'subscription']
    ordering_fields = ['created_at', 'paid_at', 'amount']
    ordering = ['-created_at']
    http_method_names = ['get', 'post']
    
    def get_queryset(self):
        """Filtrer les paiements selon le rôle"""
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(subscription__user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PaymentListSerializer
        elif self.action == 'initiate':
            return PaymentInitiateSerializer
        elif self.action == 'update_status':
            return PaymentStatusUpdateSerializer
        return PaymentDetailSerializer
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initier un paiement avec PayDunya"""
        serializer = PaymentInitiateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        subscription = serializer.validated_data['subscription']
        
        # Générer un ID de transaction unique
        transaction_id = f"PAY-{uuid.uuid4().hex[:16].upper()}"
        
        # Créer le paiement
        payment = Payment.objects.create(
            subscription=subscription,
            amount=subscription.plan.price,
            payment_method='paydunya',
            status='pending',
            transaction_id=transaction_id
        )
        
        # Initialiser PayDunya
        paydunya = PayDunyaService()
        
        # URLs de callback
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        callback_url = f"{site_url}/api/v1/payments/callback/"
        return_url = f"{site_url}/payment/success/{payment.id}/"
        cancel_url = f"{site_url}/payment/cancel/{payment.id}/"
        
        # Créer la facture PayDunya
        result = paydunya.create_invoice(
            payment=payment,
            user=request.user,
            callback_url=callback_url,
            return_url=return_url,
            cancel_url=cancel_url
        )
        
        if result['success']:
            # Sauvegarder le token PayDunya
            payment.payment_provider_response = {
                'token': result['token'],
                'response_code': result['response_code']
            }
            payment.save()
            
            response_data = {
                'message': 'Paiement initié avec succès',
                'payment': PaymentDetailSerializer(
                    payment,
                    context={'request': request}
                ).data,
                'payment_url': result['invoice_url'],
                'token': result['token']
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            payment.status = 'failed'
            payment.payment_provider_response = result
            payment.save()
            
            return Response({
                'error': 'Erreur lors de l\'initialisation du paiement',
                'details': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post', 'get'], permission_classes=[AllowAny])
    def callback(self, request):
        """Callback PayDunya (webhook)"""
        # PayDunya envoie le token dans les paramètres
        token = request.data.get('token') or request.query_params.get('token')
        
        if not token:
            return Response(
                {'error': 'Token manquant'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier le statut auprès de PayDunya
        paydunya = PayDunyaService()
        result = paydunya.confirm_invoice(token)
        
        if not result['success']:
            return Response(
                {'error': 'Erreur lors de la vérification du paiement'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer le payment_id des custom_data
        custom_data = result.get('custom_data', {})
        payment_id = custom_data.get('payment_id')
        
        if not payment_id:
            return Response(
                {'error': 'ID de paiement introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            payment = Payment.objects.get(id=payment_id)
            
            # Statut PayDunya: completed, pending, cancelled
            paydunya_status = result.get('status', '').lower()
            
            if paydunya_status == 'completed':
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.payment_provider_response = result
                payment.save()
                
                # Activer l'abonnement
                subscription = payment.subscription
                subscription.status = 'active'
                subscription.save()
                
                # Notification de succès
                create_notification(
                    user=subscription.user,
                    notification_type='subscription_expiring',
                    title='Paiement confirmé',
                    message=f'Votre paiement de {payment.amount} FCFA a été confirmé. Votre abonnement {subscription.plan.name} est maintenant actif.',
                    link=f'/subscriptions/{subscription.id}'
                )
                
                return Response({
                    'message': 'Paiement confirmé avec succès',
                    'payment_id': payment.id
                })
                
            elif paydunya_status == 'cancelled':
                payment.status = 'failed'
                payment.payment_provider_response = result
                payment.save()
                
                # Notification d'échec
                create_notification(
                    user=payment.subscription.user,
                    notification_type='subscription_expiring',
                    title='Paiement annulé',
                    message='Votre paiement a été annulé. Veuillez réessayer.',
                    link=f'/payments/{payment.id}'
                )
                
                return Response({
                    'message': 'Paiement annulé',
                    'payment_id': payment.id
                })
            else:
                # Statut en attente ou autre
                payment.payment_provider_response = result
                payment.save()
                
                return Response({
                    'message': 'Paiement en cours de traitement',
                    'payment_id': payment.id,
                    'status': paydunya_status
                })
            
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Paiement introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def verify(self, request, pk=None):
        """Vérifier le statut d'un paiement auprès de PayDunya"""
        payment = self.get_object()
        
        if not payment.payment_provider_response or 'token' not in payment.payment_provider_response:
            return Response(
                {'error': 'Token PayDunya introuvable'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = payment.payment_provider_response['token']
        paydunya = PayDunyaService()
        result = paydunya.confirm_invoice(token)
        
        if result['success']:
            return Response({
                'payment_id': payment.id,
                'paydunya_status': result.get('status'),
                'response': result
            })
        else:
            return Response({
                'error': 'Erreur lors de la vérification',
                'details': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'un paiement (Admin)"""
        payment = self.get_object()
        serializer = PaymentStatusUpdateSerializer(
            payment,
            data=request.data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        # Si le paiement est complété, activer l'abonnement
        if serializer.validated_data.get('status') == 'completed':
            subscription = payment.subscription
            subscription.status = 'active'
            subscription.save()
            
            # Notification
            create_notification(
                user=subscription.user,
                notification_type='subscription_expiring',
                title='Abonnement activé',
                message=f'Votre abonnement {subscription.plan.name} est maintenant actif.',
                link=f'/subscriptions/{subscription.id}'
            )
        
        return Response({
            'message': 'Statut du paiement mis à jour',
            'data': PaymentDetailSerializer(
                payment,
                context={'request': request}
            ).data
        })
    
    @action(detail=False, methods=['get'])
    def my_payments(self, request):
        """Historique des paiements de l'utilisateur"""
        payments = Payment.objects.filter(
            subscription__user=request.user
        ).order_by('-created_at')
        
        serializer = PaymentListSerializer(
            payments,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def statistics(self, request):
        """Statistiques des paiements (Admin)"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        payments = Payment.objects.filter(status='completed')
        
        if start_date:
            payments = payments.filter(paid_at__gte=start_date)
        if end_date:
            payments = payments.filter(paid_at__lte=end_date)
        
        stats = {
            'total_payments': payments.count(),
            'total_revenue': payments.aggregate(Sum('amount'))['amount__sum'] or 0,
            'by_method': {},
            'by_status': {}
        }
        
        # Statistiques par méthode de paiement
        for method, _ in Payment.PAYMENT_METHOD_CHOICES:
            count = Payment.objects.filter(
                payment_method=method,
                status='completed'
            ).count()
            revenue = Payment.objects.filter(
                payment_method=method,
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            stats['by_method'][method] = {
                'count': count,
                'revenue': float(revenue)
            }
        
        # Statistiques par statut
        for status_val, _ in Payment.STATUS_CHOICES:
            count = Payment.objects.filter(status=status_val).count()
            stats['by_status'][status_val] = count
        
        return Response(stats)


# ============================================================================
# Admin Dashboard ViewSet
# ============================================================================

class SubscriptionAdminViewSet(viewsets.ViewSet):
    """ViewSet pour les statistiques d'administration"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dashboard admin avec statistiques globales"""
        now = timezone.now()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total_subscriptions = Subscription.objects.count()
        active_subscriptions = Subscription.objects.filter(
            status__in=['trial', 'active'],
            end_date__gt=now
        ).count()
        trial_subscriptions = Subscription.objects.filter(
            status='trial',
            end_date__gt=now
        ).count()
        expired_subscriptions = Subscription.objects.filter(
            status='expired'
        ).count()
        
        total_revenue = Payment.objects.filter(
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        revenue_this_month = Payment.objects.filter(
            status='completed',
            paid_at__gte=first_day_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        trials = Subscription.objects.filter(is_trial=True).count()
        paid = Subscription.objects.filter(is_trial=False, status='active').count()
        conversion_rate = (paid / trials * 100) if trials > 0 else 0
        
        data = {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'trial_subscriptions': trial_subscriptions,
            'expired_subscriptions': expired_subscriptions,
            'total_revenue': float(total_revenue),
            'revenue_this_month': float(revenue_this_month),
            'conversion_rate': round(conversion_rate, 2)
        }
        
        serializer = SubscriptionStatsSerializer(data)
        return Response(serializer.data)