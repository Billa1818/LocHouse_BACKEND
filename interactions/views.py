from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.utils import timezone

from .models import AvailabilityRequest, ContactMessage, Review, Favorite
from .serializers import (
    AvailabilityRequestListSerializer,
    AvailabilityRequestDetailSerializer,
    AvailabilityRequestCreateSerializer,
    AvailabilityRequestStatusUpdateSerializer,
    ContactMessageListSerializer,
    ContactMessageDetailSerializer,
    ContactMessageCreateSerializer,
    ReviewListSerializer,
    ReviewDetailSerializer,
    ReviewCreateUpdateSerializer,
    ReviewModerationSerializer,
    FavoriteListSerializer,
    FavoriteCreateSerializer,
    ListingReviewStatsSerializer
)
from .permissions import IsOwnerOrReadOnly, IsRequestOwnerOrListingOwner, IsReviewAuthor, IsAdmin


# ============================================================================
# AvailabilityRequest ViewSet
# ============================================================================

class AvailabilityRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les demandes de disponibilité.
    - Locataires: créer des demandes, voir leurs propres demandes
    - Propriétaires: voir les demandes reçues, mettre à jour le statut
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'listing']
    ordering_fields = ['created_at', 'check_in_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filtrer les demandes selon le rôle:
        - Locataire: ses propres demandes
        - Propriétaire: demandes pour ses annonces
        - Admin: toutes les demandes
        """
        user = self.request.user
        
        if user.is_staff:
            return AvailabilityRequest.objects.all()
        
        if user.user_type == 'proprietaire':
            # Propriétaire voit les demandes pour ses annonces
            return AvailabilityRequest.objects.filter(
                listing__owner=user
            )
        
        # Locataire voit ses propres demandes
        return AvailabilityRequest.objects.filter(requester=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AvailabilityRequestListSerializer
        elif self.action == 'create':
            return AvailabilityRequestCreateSerializer
        elif self.action == 'update_status':
            return AvailabilityRequestStatusUpdateSerializer
        return AvailabilityRequestDetailSerializer
    
    def perform_create(self, serializer):
        """Créer une demande et envoyer notification au propriétaire"""
        request_obj = serializer.save()
        
        # Vérifier si les notifications sont activées pour ce groupe
        if request_obj.listing.are_notifications_enabled():
            # TODO: Envoyer notification email/SMS au propriétaire
            request_obj.owner_notified = True
            request_obj.save()
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Obtenir toutes les demandes de l'utilisateur connecté (locataire)"""
        requests = AvailabilityRequest.objects.filter(
            requester=request.user
        ).order_by('-created_at')
        
        serializer = AvailabilityRequestListSerializer(
            requests,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def received_requests(self, request):
        """Obtenir les demandes reçues (propriétaire)"""
        if request.user.user_type != 'proprietaire':
            return Response(
                {'error': 'Accès réservé aux propriétaires'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        requests = AvailabilityRequest.objects.filter(
            listing__owner=request.user
        ).order_by('-created_at')
        
        serializer = AvailabilityRequestListSerializer(
            requests,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'une demande (propriétaire uniquement)"""
        availability_request = self.get_object()
        
        # Vérifier que c'est le propriétaire de l'annonce
        if availability_request.listing.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à modifier cette demande'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AvailabilityRequestStatusUpdateSerializer(
            availability_request,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Statut mis à jour avec succès',
                'data': AvailabilityRequestDetailSerializer(
                    availability_request,
                    context={'request': request}
                ).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# ContactMessage ViewSet
# ============================================================================

class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les messages de contact.
    - Création de messages (locataires -> propriétaires)
    - Consultation des conversations
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['listing', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filtrer les messages:
        - Utilisateur voit les messages qu'il a envoyés ou reçus
        """
        user = self.request.user
        
        if user.is_staff:
            return ContactMessage.objects.all()
        
        return ContactMessage.objects.filter(
            Q(sender=user) | Q(receiver=user)
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ContactMessageListSerializer
        elif self.action == 'create':
            return ContactMessageCreateSerializer
        return ContactMessageDetailSerializer
    
    def perform_create(self, serializer):
        """Créer un message et envoyer notification"""
        message = serializer.save()
        
        # Si c'est le premier contact, débloquer les infos de contact
        if message.is_first_contact:
            # TODO: Logique pour révéler email/téléphone du propriétaire
            pass
        
        # Vérifier si les notifications sont activées
        if message.listing.are_notifications_enabled():
            # TODO: Envoyer notification au destinataire
            pass
    
    def retrieve(self, request, *args, **kwargs):
        """Marquer comme lu lors de la lecture"""
        instance = self.get_object()
        
        # Marquer comme lu si c'est le destinataire qui lit
        if instance.receiver == request.user and not instance.is_read:
            instance.is_read = True
            instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """Obtenir la liste des conversations groupées par annonce"""
        user = request.user
        
        # Récupérer tous les messages de l'utilisateur
        messages = ContactMessage.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).order_by('-created_at')
        
        # Grouper par annonce
        conversations = {}
        for message in messages:
            listing_id = message.listing.id
            if listing_id not in conversations:
                conversations[listing_id] = {
                    'listing_id': listing_id,
                    'listing_title': message.listing.title,
                    'last_message': message.message,
                    'last_message_at': message.created_at,
                    'unread_count': 0,
                    'other_user': None
                }
            
            # Compter les non lus (reçus uniquement)
            if message.receiver == user and not message.is_read:
                conversations[listing_id]['unread_count'] += 1
            
            # Déterminer l'autre utilisateur
            if message.sender == user:
                conversations[listing_id]['other_user'] = message.receiver.get_full_name()
            else:
                conversations[listing_id]['other_user'] = message.sender.get_full_name()
        
        return Response(list(conversations.values()))
    
    @action(detail=False, methods=['get'])
    def by_listing(self, request):
        """Obtenir les messages d'une conversation spécifique"""
        listing_id = request.query_params.get('listing_id')
        
        if not listing_id:
            return Response(
                {'error': 'listing_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        messages = ContactMessage.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user),
            listing_id=listing_id
        ).order_by('created_at')
        
        # Marquer comme lus les messages reçus
        messages.filter(receiver=request.user, is_read=False).update(is_read=True)
        
        serializer = ContactMessageListSerializer(
            messages,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Nombre de messages non lus"""
        count = ContactMessage.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})


# ============================================================================
# Review ViewSet
# ============================================================================

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les avis.
    - Public: voir les avis approuvés
    - Locataires: créer/modifier leurs avis
    - Admin: modérer les avis
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['listing', 'rating', 'status']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filtrer les avis selon le rôle:
        - Public: avis approuvés uniquement
        - Auteur: ses propres avis (tous statuts)
        - Admin: tous les avis
        """
        if self.request.user.is_staff:
            return Review.objects.all()
        
        if self.request.user.is_authenticated:
            # Utilisateurs authentifiés voient:
            # - Les avis approuvés (tous)
            # - Leurs propres avis (tous statuts)
            return Review.objects.filter(
                Q(status='approved') | Q(author=self.request.user)
            )
        
        # Public: avis approuvés uniquement
        return Review.objects.filter(status='approved')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ReviewListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ReviewCreateUpdateSerializer
        elif self.action == 'moderate':
            return ReviewModerationSerializer
        return ReviewDetailSerializer
    
    def get_permissions(self):
        """Permissions selon l'action"""
        if self.action in ['create']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsReviewAuthor()]
        elif self.action in ['moderate', 'pending_reviews']:
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Obtenir les avis de l'utilisateur connecté"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentification requise'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        reviews = Review.objects.filter(author=request.user)
        serializer = ReviewListSerializer(
            reviews,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_listing(self, request):
        """Obtenir les avis d'une annonce spécifique"""
        listing_id = request.query_params.get('listing_id')
        
        if not listing_id:
            return Response(
                {'error': 'listing_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = Review.objects.filter(
            listing_id=listing_id,
            status='approved'
        ).order_by('-created_at')
        
        serializer = ReviewListSerializer(
            reviews,
            many=True,
            context={'request': request}
        )
        
        # Ajouter les statistiques
        stats = reviews.aggregate(
            total=Count('id'),
            average=Avg('rating')
        )
        
        return Response({
            'reviews': serializer.data,
            'statistics': {
                'total_reviews': stats['total'] or 0,
                'average_rating': round(stats['average'] or 0, 1)
            }
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def moderate(self, request, pk=None):
        """Modérer un avis (Admin uniquement)"""
        review = self.get_object()
        serializer = ReviewModerationSerializer(
            review,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Avis modéré avec succès',
                'data': ReviewDetailSerializer(review, context={'request': request}).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def pending_reviews(self, request):
        """Liste des avis en attente de modération (Admin)"""
        pending = Review.objects.filter(status='pending').order_by('-created_at')
        serializer = ReviewListSerializer(
            pending,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques globales des avis"""
        listing_id = request.query_params.get('listing_id')
        
        if not listing_id:
            return Response(
                {'error': 'listing_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = Review.objects.filter(
            listing_id=listing_id,
            status='approved'
        )
        
        # Calculer les statistiques
        total_reviews = reviews.count()
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Distribution des notes
        rating_distribution = {
            '5': reviews.filter(rating=5).count(),
            '4': reviews.filter(rating=4).count(),
            '3': reviews.filter(rating=3).count(),
            '2': reviews.filter(rating=2).count(),
            '1': reviews.filter(rating=1).count(),
        }
        
        # Avis récents
        recent_reviews = reviews.order_by('-created_at')[:5]
        
        return Response({
            'total_reviews': total_reviews,
            'average_rating': round(average_rating, 1),
            'rating_distribution': rating_distribution,
            'recent_reviews': ReviewListSerializer(
                recent_reviews,
                many=True,
                context={'request': request}
            ).data
        })


# ============================================================================
# Favorite ViewSet
# ============================================================================

class FavoriteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les favoris.
    - Utilisateurs authentifiés peuvent gérer leurs favoris
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'delete']  # Pas de PUT/PATCH
    
    def get_queryset(self):
        """Filtrer les favoris de l'utilisateur connecté"""
        return Favorite.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FavoriteCreateSerializer
        return FavoriteListSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Supprimer un favori"""
        instance = self.get_object()
        
        # Vérifier que c'est bien l'utilisateur propriétaire
        if instance.user != request.user:
            return Response(
                {'error': 'Vous ne pouvez supprimer que vos propres favoris'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.delete()
        return Response(
            {'message': 'Favori supprimé avec succès'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Ajouter/retirer un favori (toggle)"""
        listing_id = request.data.get('listing_id')
        
        if not listing_id:
            return Response(
                {'error': 'listing_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            favorite = Favorite.objects.get(
                user=request.user,
                listing_id=listing_id
            )
            # Existe déjà, on supprime
            favorite.delete()
            return Response({
                'message': 'Retiré des favoris',
                'is_favorite': False
            })
        except Favorite.DoesNotExist:
            # N'existe pas, on ajoute
            serializer = FavoriteCreateSerializer(
                data={'listing': listing_id},
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Ajouté aux favoris',
                    'is_favorite': True,
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """Vérifier si une annonce est dans les favoris"""
        listing_id = request.query_params.get('listing_id')
        
        if not listing_id:
            return Response(
                {'error': 'listing_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_favorite = Favorite.objects.filter(
            user=request.user,
            listing_id=listing_id
        ).exists()
        
        return Response({'is_favorite': is_favorite})