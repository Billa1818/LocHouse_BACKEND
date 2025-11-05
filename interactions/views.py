# ============================================================================
# interactions/views.py
# ============================================================================
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import AvailabilityRequest, ContactMessage, Review, Favorite
from .serializers import (
    AvailabilityRequestSerializer,
    AvailabilityRequestUpdateSerializer,
    ContactMessageSerializer,
    ContactMessageListSerializer,
    ReviewSerializer,
    ReviewModerationSerializer,
    FavoriteSerializer
)
from listings.models import Listing


# ============================================================================
# CUSTOM PERMISSIONS
# ============================================================================
class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission personnalisée : propriétaire ou lecture seule"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Pour AvailabilityRequest, vérifier si c'est le requester ou le owner du listing
        if isinstance(obj, AvailabilityRequest):
            return obj.requester == request.user or obj.listing.owner == request.user
        
        # Pour les autres modèles
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'author'):
            return obj.author == request.user
        
        return False


class IsListingOwner(permissions.BasePermission):
    """Permission : propriétaire du listing concerné"""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'listing'):
            return obj.listing.owner == request.user
        return False


class IsAdminUser(permissions.BasePermission):
    """Permission : utilisateur admin"""
    
    def has_permission(self, request, view):
        return request.user and request.user.user_type == 'admin'


# ============================================================================
# AVAILABILITY REQUEST VIEWSET
# ============================================================================
class AvailabilityRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les demandes de disponibilité
    
    - Locataires : peuvent créer des demandes
    - Propriétaires : peuvent voir les demandes pour leurs annonces et modifier le statut
    - Admins : accès complet
    """
    queryset = AvailabilityRequest.objects.select_related(
        'listing', 'requester', 'listing__owner', 'listing__property_group'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'listing']
    ordering_fields = ['created_at', 'check_in_date']
    search_fields = ['message', 'listing__title']
    
    def get_serializer_class(self):
        if self.action == 'update_status':
            return AvailabilityRequestUpdateSerializer
        return AvailabilityRequestSerializer
    
    def get_queryset(self):
        """Filtrer selon le type d'utilisateur"""
        user = self.request.user
        
        if user.user_type == 'admin':
            return self.queryset
        elif user.user_type == 'proprietaire':
            # Propriétaires : voir les demandes pour leurs annonces
            return self.queryset.filter(listing__owner=user)
        else:
            # Locataires : voir leurs propres demandes
            return self.queryset.filter(requester=user)
    
    def perform_create(self, serializer):
        """Associer le requester à la demande"""
        serializer.save(requester=self.request.user)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsListingOwner])
    def update_status(self, request, pk=None):
        """
        Mise à jour du statut de la demande (propriétaire uniquement)
        
        PATCH /api/availability-requests/{id}/update_status/
        Body: {"status": "contacted"}
        """
        availability_request = self.get_object()
        serializer = self.get_serializer(availability_request, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Statut mis à jour avec succès',
            'data': AvailabilityRequestSerializer(availability_request).data
        })
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """
        Liste des demandes de l'utilisateur connecté
        
        GET /api/availability-requests/my_requests/
        """
        requests = self.get_queryset().filter(requester=request.user)
        page = self.paginate_queryset(requests)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def received_requests(self, request):
        """
        Demandes reçues par le propriétaire
        
        GET /api/availability-requests/received_requests/
        """
        if request.user.user_type != 'proprietaire':
            return Response(
                {'error': 'Cette action est réservée aux propriétaires'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        requests = self.get_queryset().filter(listing__owner=request.user)
        
        # Filtres optionnels
        status_filter = request.query_params.get('status')
        if status_filter:
            requests = requests.filter(status=status_filter)
        
        listing_id = request.query_params.get('listing_id')
        if listing_id:
            requests = requests.filter(listing_id=listing_id)
        
        page = self.paginate_queryset(requests)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)


# ============================================================================
# CONTACT MESSAGE VIEWSET
# ============================================================================
class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les messages de contact
    
    - Locataires : peuvent envoyer des messages
    - Propriétaires : peuvent voir et répondre aux messages
    - Révélation du contact après le premier message
    """
    queryset = ContactMessage.objects.select_related(
        'listing', 'sender', 'receiver', 'listing__owner', 'listing__property_group'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['listing', 'is_read']
    ordering_fields = ['created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ContactMessageListSerializer
        return ContactMessageSerializer
    
    def get_queryset(self):
        """Filtrer les messages de l'utilisateur"""
        user = self.request.user
        
        if user.user_type == 'admin':
            return self.queryset
        
        # Messages où l'utilisateur est sender ou receiver
        return self.queryset.filter(Q(sender=user) | Q(receiver=user))
    
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """
        Liste des conversations groupées par listing
        
        GET /api/messages/conversations/
        """
        user = request.user
        
        # Récupérer tous les listings où l'utilisateur a des messages
        messages = self.get_queryset().order_by('listing', '-created_at')
        
        # Grouper par listing (garder le dernier message de chaque conversation)
        conversations = {}
        for message in messages:
            listing_id = message.listing.id
            if listing_id not in conversations:
                conversations[listing_id] = message
        
        # Sérialiser
        serializer = ContactMessageListSerializer(
            list(conversations.values()),
            many=True,
            context={'request': request}
        )
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def conversation_detail(self, request):
        """
        Détail d'une conversation pour un listing spécifique
        
        GET /api/messages/conversation_detail/?listing_id=123
        """
        listing_id = request.query_params.get('listing_id')
        
        if not listing_id:
            return Response(
                {'error': 'listing_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer tous les messages de cette conversation
        messages = self.get_queryset().filter(listing_id=listing_id).order_by('created_at')
        
        if not messages.exists():
            return Response(
                {'error': 'Aucune conversation trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Marquer comme lu les messages reçus
        messages.filter(receiver=request.user, is_read=False).update(is_read=True)
        
        serializer = ContactMessageSerializer(
            messages,
            many=True,
            context={'request': request}
        )
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        """
        Marquer un message comme lu
        
        PATCH /api/messages/{id}/mark_as_read/
        """
        message = self.get_object()
        
        # Vérifier que c'est bien le receiver
        if message.receiver != request.user:
            return Response(
                {'error': 'Vous ne pouvez marquer comme lu que vos messages reçus'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_read = True
        message.save(update_fields=['is_read'])
        
        return Response({'message': 'Message marqué comme lu'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Nombre de messages non lus
        
        GET /api/messages/unread_count/
        """
        count = self.get_queryset().filter(
            receiver=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})


# ============================================================================
# REVIEW VIEWSET
# ============================================================================
class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les avis
    
    - Locataires : peuvent créer et modifier leurs avis
    - Public : peut voir les avis approuvés
    - Admins : peuvent modérer les avis
    """
    queryset = Review.objects.select_related('listing', 'author')
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['listing', 'status', 'rating']
    ordering_fields = ['created_at', 'rating']
    
    def get_permissions(self):
        """Permissions selon l'action"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['moderate', 'pending_reviews']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'moderate':
            return ReviewModerationSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        """Filtrer selon le contexte"""
        user = self.request.user
        
        # Public : seulement les avis approuvés
        if not user.is_authenticated:
            return self.queryset.filter(status='approved')
        
        # Admin : tous les avis
        if user.user_type == 'admin':
            return self.queryset
        
        # Propriétaires : avis approuvés + avis sur leurs annonces
        if user.user_type == 'proprietaire':
            return self.queryset.filter(
                Q(status='approved') | Q(listing__owner=user)
            )
        
        # Locataires : avis approuvés + leurs propres avis
        return self.queryset.filter(
            Q(status='approved') | Q(author=user)
        )
    
    def perform_create(self, serializer):
        """Associer l'auteur"""
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsAdminUser])
    def moderate(self, request, pk=None):
        """
        Modérer un avis (admin uniquement)
        
        PATCH /api/reviews/{id}/moderate/
        Body: {"status": "approved"} ou {"status": "rejected", "rejection_reason": "..."}
        """
        review = self.get_object()
        serializer = self.get_serializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Avis modéré avec succès',
            'data': ReviewSerializer(review).data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def pending_reviews(self, request):
        """
        Liste des avis en attente de modération
        
        GET /api/reviews/pending_reviews/
        """
        reviews = self.queryset.filter(status='pending').order_by('-created_at')
        page = self.paginate_queryset(reviews)
        
        if page is not None:
            serializer = ReviewSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """
        Avis de l'utilisateur connecté
        
        GET /api/reviews/my_reviews/
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication requise'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        reviews = self.queryset.filter(author=request.user)
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def listing_stats(self, request):
        """
        Statistiques des avis pour un listing
        
        GET /api/reviews/listing_stats/?listing_id=123
        """
        listing_id = request.query_params.get('listing_id')
        
        if not listing_id:
            return Response(
                {'error': 'listing_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = self.queryset.filter(listing_id=listing_id, status='approved')
        
        stats = reviews.aggregate(
            average_rating=Avg('rating'),
            total_reviews=Count('id')
        )
        
        # Distribution des notes
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[f'rating_{i}'] = reviews.filter(rating=i).count()
        
        return Response({
            'average_rating': round(stats['average_rating'], 1) if stats['average_rating'] else 0,
            'total_reviews': stats['total_reviews'],
            'rating_distribution': rating_distribution
        })


# ============================================================================
# FAVORITE VIEWSET
# ============================================================================
class FavoriteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les favoris
    
    - Utilisateurs authentifiés : peuvent gérer leurs favoris
    """
    queryset = Favorite.objects.select_related('listing', 'user', 'listing__owner')
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']  # Pas de PUT/PATCH
    
    def get_queryset(self):
        """Filtrer les favoris de l'utilisateur"""
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        Ajouter/retirer des favoris
        
        POST /api/favorites/toggle/
        Body: {"listing": 123}
        """
        listing_id = request.data.get('listing')
        
        if not listing_id:
            return Response(
                {'error': 'listing est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        listing = get_object_or_404(Listing, id=listing_id, status='published')
        
        # Vérifier si déjà en favoris
        favorite = Favorite.objects.filter(user=request.user, listing=listing).first()
        
        if favorite:
            # Retirer des favoris
            favorite.delete()
            return Response({
                'message': 'Retiré des favoris',
                'is_favorite': False
            })
        else:
            # Ajouter aux favoris
            favorite = Favorite.objects.create(user=request.user, listing=listing)
            return Response({
                'message': 'Ajouté aux favoris',
                'is_favorite': True,
                'data': self.get_serializer(favorite).data
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        Vérifier si un listing est en favoris
        
        GET /api/favorites/check/?listing_id=123
        """
        listing_id = request.query_params.get('listing_id')
        
        if not listing_id:
            return Response(
                {'error': 'listing_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_favorite = self.get_queryset().filter(listing_id=listing_id).exists()
        
        return Response({'is_favorite': is_favorite})