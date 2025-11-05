from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from interactions.models import Favorite
from .models import PropertyGroup, Listing, ListingAmenity, ListingMedia
from .serializers import (
    PropertyGroupListSerializer,
    PropertyGroupDetailSerializer,
    PropertyGroupCreateUpdateSerializer,
    ListingListSerializer,
    ListingDetailSerializer,
    ListingCreateUpdateSerializer,
    ListingStatusUpdateSerializer,
    ListingAmenitySerializer,
    ListingMediaSerializer
)
from .filters import ListingFilter
from .permissions import IsOwnerOrReadOnly, IsOwner, IsAdmin


# ============================================================================
# PropertyGroup ViewSet
# ============================================================================

class PropertyGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les groupes de propriétés.
    CRUD complet pour les propriétaires.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les groupes par propriétaire"""
        if self.request.user.is_staff:
            # Admin voit tous les groupes
            return PropertyGroup.objects.all().annotate(
                listings_count=Count('listings')
            )
        # Propriétaires voient seulement leurs groupes
        return PropertyGroup.objects.filter(
            owner=self.request.user
        ).annotate(
            listings_count=Count('listings')
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyGroupListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PropertyGroupCreateUpdateSerializer
        return PropertyGroupDetailSerializer
    
    def perform_create(self, serializer):
        """Associer automatiquement le propriétaire"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_notifications(self, request, pk=None):
        """Activer/désactiver les notifications pour un groupe"""
        group = self.get_object()
        group.notifications_enabled = not group.notifications_enabled
        group.save()
        
        serializer = self.get_serializer(group)
        return Response({
            'message': f"Notifications {'activées' if group.notifications_enabled else 'désactivées'}",
            'data': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def listings(self, request, pk=None):
        """Obtenir toutes les annonces d'un groupe"""
        group = self.get_object()
        listings = group.listings.all()
        
        serializer = ListingListSerializer(
            listings,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Statistiques d'un groupe"""
        group = self.get_object()
        listings = group.listings.all()
        
        stats = {
            'total_listings': listings.count(),
            'published_listings': listings.filter(status='published').count(),
            'pending_listings': listings.filter(status='pending').count(),
            'total_views': sum(l.views_count for l in listings),
            'notifications_enabled': group.notifications_enabled
        }
        
        return Response(stats)


# ============================================================================
# Listing ViewSet
# ============================================================================

class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les annonces.
    - Liste publique (lecture seule) pour les locataires
    - CRUD complet pour les propriétaires
    - Validation/modération pour les admins
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description', 'city', 'district', 'property_name']
    ordering_fields = ['created_at', 'published_at', 'daily_price', 'monthly_price', 'views_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filtrer les annonces selon le rôle:
        - Public: annonces publiées uniquement
        - Propriétaire: ses propres annonces (tous statuts)
        - Admin: toutes les annonces
        """
        if self.action == 'list' and not self.request.user.is_authenticated:
            # Utilisateurs non authentifiés: annonces publiées uniquement
            return Listing.objects.filter(status='published')
        
        if self.request.user.is_staff:
            # Admin voit tout
            return Listing.objects.all()
        
        if self.request.user.is_authenticated:
            # Utilisateurs authentifiés voient:
            # - Les annonces publiées (tous propriétaires)
            # - Leurs propres annonces (tous statuts)
            return Listing.objects.filter(
                Q(status='published') | Q(owner=self.request.user)
            )
        
        return Listing.objects.filter(status='published')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ListingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ListingCreateUpdateSerializer
        elif self.action == 'update_status':
            return ListingStatusUpdateSerializer
        return ListingDetailSerializer
    
    def get_permissions(self):
        """Permissions selon l'action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwner()]
        elif self.action in ['update_status', 'pending_listings']:
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]
    
    def perform_create(self, serializer):
        """Créer une annonce associée au propriétaire"""
        serializer.save(owner=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Incrémenter le compteur de vues lors de la consultation"""
        instance = self.get_object()
        
        # Incrémenter seulement si ce n'est pas le propriétaire
        if not request.user.is_authenticated or request.user != instance.owner:
            instance.views_count += 1
            instance.save(update_fields=['views_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        """Obtenir toutes les annonces du propriétaire connecté"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentification requise'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        listings = Listing.objects.filter(owner=request.user)
        serializer = ListingListSerializer(
            listings,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_dashboard(self, request):
        """Dashboard propriétaire: statistiques et groupes"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentification requise'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        listings = Listing.objects.filter(owner=request.user)
        groups = PropertyGroup.objects.filter(owner=request.user).annotate(
            listings_count=Count('listings')
        )
        
        dashboard = {
            'total_listings': listings.count(),
            'published': listings.filter(status='published').count(),
            'pending': listings.filter(status='pending').count(),
            'draft': listings.filter(status='draft').count(),
            'rejected': listings.filter(status='rejected').count(),
            'total_views': sum(l.views_count for l in listings),
            'groups': PropertyGroupListSerializer(groups, many=True).data
        }
        
        return Response(dashboard)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def update_status(self, request, pk=None):
        """
        Mettre à jour le statut d'une annonce (Admin uniquement).
        Permet de valider, rejeter ou archiver une annonce.
        """
        listing = self.get_object()
        serializer = ListingStatusUpdateSerializer(
            listing,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Si publication, enregistrer la date
            if serializer.validated_data.get('status') == 'published':
                listing.published_at = timezone.now()
                listing.save()
            
            return Response({
                'message': 'Statut mis à jour avec succès',
                'data': ListingDetailSerializer(listing, context={'request': request}).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def pending_listings(self, request):
        """Liste des annonces en attente de validation (Admin)"""
        pending = Listing.objects.filter(status='pending').order_by('-created_at')
        serializer = ListingListSerializer(
            pending,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_to_favorites(self, request, pk=None):
        """Ajouter aux favoris d'un locataire"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentification requise'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Ajouter à la liste des favoris
        listing = self.get_object()
        Favorite.objects.get_or_create(user=request.user, listing=listing)

        return Response({
            'message': 'Ajouté aux favoris avec succès',
            'listing_id': pk
        })
    
    @action(detail=True, methods=['delete'])
    def delete_media(self, request, pk=None):
        """Supprimer un média d'une annonce"""
        listing = self.get_object()
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response(
                {'error': 'media_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            media = ListingMedia.objects.get(id=media_id, listing=listing)
            media.delete()
            return Response({'message': 'Média supprimé avec succès'})
        except ListingMedia.DoesNotExist:
            return Response(
                {'error': 'Média introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============================================================================
# ListingAmenity ViewSet
# ============================================================================

class ListingAmenityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les équipements (lecture seule).
    Liste des équipements disponibles pour les filtres et l'ajout.
    """
    queryset = ListingAmenity.objects.all()
    serializer_class = ListingAmenitySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']