from rest_framework import serializers
from django.utils import timezone
from .models import AvailabilityRequest, ContactMessage, Review, Favorite
from listings.models import Listing
from accounts.models import User


# ============================================================================
# AvailabilityRequest Serializers
# ============================================================================

class AvailabilityRequestListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des demandes de disponibilité"""
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_id = serializers.IntegerField(source='listing.id', read_only=True)
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    requester_email = serializers.EmailField(source='requester.email', read_only=True)
    
    class Meta:
        model = AvailabilityRequest
        fields = [
            'id', 'listing_id', 'listing_title', 'requester_name', 
            'requester_email', 'requester_phone', 'message',
            'check_in_date', 'check_out_date', 'guests_count',
            'status', 'owner_notified', 'created_at'
        ]
        read_only_fields = ['id', 'owner_notified', 'created_at']


class AvailabilityRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une demande"""
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_owner = serializers.CharField(source='listing.owner.get_full_name', read_only=True)
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    requester_email = serializers.EmailField(source='requester.email', read_only=True)
    
    class Meta:
        model = AvailabilityRequest
        fields = '__all__'
        read_only_fields = ['id', 'requester', 'owner_notified', 'created_at']


class AvailabilityRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une demande de disponibilité"""
    
    class Meta:
        model = AvailabilityRequest
        fields = [
            'listing', 'requester_phone', 'message',
            'check_in_date', 'check_out_date', 'guests_count'
        ]
    
    def validate_listing(self, value):
        """Vérifier que l'annonce existe et est publiée"""
        if value.status != 'published':
            raise serializers.ValidationError(
                "Cette annonce n'est pas disponible pour le moment."
            )
        return value
    
    def validate(self, data):
        """Validations croisées"""
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        
        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError({
                    'check_out_date': "La date de départ doit être après la date d'arrivée."
                })
            
            if check_in < timezone.now().date():
                raise serializers.ValidationError({
                    'check_in_date': "La date d'arrivée ne peut pas être dans le passé."
                })
        
        if data.get('guests_count', 0) <= 0:
            raise serializers.ValidationError({
                'guests_count': "Le nombre de personnes doit être supérieur à 0."
            })
        
        return data
    
    def create(self, validated_data):
        """Créer la demande avec le requester automatique"""
        validated_data['requester'] = self.context['request'].user
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class AvailabilityRequestStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mise à jour du statut (Propriétaire)"""
    
    class Meta:
        model = AvailabilityRequest
        fields = ['status']
    
    def validate_status(self, value):
        if value not in ['pending', 'contacted', 'closed']:
            raise serializers.ValidationError("Statut invalide.")
        return value


# ============================================================================
# ContactMessage Serializers
# ============================================================================

class ContactMessageListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des messages"""
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.get_full_name', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'listing', 'listing_title', 'sender', 'sender_name',
            'receiver', 'receiver_name', 'message', 'is_first_contact',
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'created_at']


class ContactMessageDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un message"""
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    receiver_name = serializers.CharField(source='receiver.get_full_name', read_only=True)
    receiver_email = serializers.EmailField(source='receiver.email', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    
    class Meta:
        model = ContactMessage
        fields = '__all__'
        read_only_fields = ['id', 'sender', 'is_read', 'created_at']


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer pour envoyer un message"""
    
    class Meta:
        model = ContactMessage
        fields = ['listing', 'receiver', 'message']
    
    def validate_listing(self, value):
        """Vérifier que l'annonce existe et est publiée"""
        if value.status != 'published':
            raise serializers.ValidationError(
                "Cette annonce n'est pas disponible."
            )
        return value
    
    def validate_receiver(self, value):
        """Vérifier que le destinataire est le propriétaire"""
        listing = self.initial_data.get('listing')
        if listing:
            try:
                listing_obj = Listing.objects.get(id=listing)
                if value != listing_obj.owner:
                    raise serializers.ValidationError(
                        "Le destinataire doit être le propriétaire de l'annonce."
                    )
            except Listing.DoesNotExist:
                raise serializers.ValidationError("Annonce introuvable.")
        return value
    
    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Le message doit contenir au moins 10 caractères."
            )
        return value
    
    def create(self, validated_data):
        """Créer le message avec détection du premier contact"""
        user = self.context['request'].user
        validated_data['sender'] = user
        
        # Vérifier si c'est le premier message de cet utilisateur pour cette annonce
        listing = validated_data['listing']
        previous_messages = ContactMessage.objects.filter(
            sender=user,
            listing=listing
        ).exists()
        
        validated_data['is_first_contact'] = not previous_messages
        
        return super().create(validated_data)


# ============================================================================
# Review Serializers
# ============================================================================

class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des avis"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'listing', 'listing_title', 'author', 'author_name',
            'rating', 'comment', 'status', 'created_at', 'approved_at'
        ]
        read_only_fields = ['id', 'author', 'status', 'created_at', 'approved_at']


class ReviewDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un avis"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['id', 'author', 'status', 'created_at', 'approved_at']


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/modifier un avis"""
    
    class Meta:
        model = Review
        fields = ['listing', 'rating', 'comment']
    
    def validate_listing(self, value):
        """Vérifier que l'annonce existe"""
        if value.status != 'published':
            raise serializers.ValidationError(
                "Impossible de laisser un avis sur cette annonce."
            )
        return value
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "La note doit être entre 1 et 5."
            )
        return value
    
    def validate_comment(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Le commentaire doit contenir au moins 20 caractères."
            )
        return value
    
    def validate(self, data):
        """Vérifier qu'un seul avis par utilisateur par annonce"""
        request = self.context.get('request')
        listing = data.get('listing')
        
        if request and listing:
            # En mode création uniquement
            if not self.instance:
                existing_review = Review.objects.filter(
                    author=request.user,
                    listing=listing
                ).exists()
                
                if existing_review:
                    raise serializers.ValidationError(
                        "Vous avez déjà laissé un avis pour cette annonce."
                    )
        
        return data
    
    def create(self, validated_data):
        """Créer un avis en attente de modération"""
        validated_data['author'] = self.context['request'].user
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class ReviewModerationSerializer(serializers.ModelSerializer):
    """Serializer pour modération des avis (Admin)"""
    
    class Meta:
        model = Review
        fields = ['status', 'rejection_reason']
    
    def validate(self, data):
        if data.get('status') == 'rejected' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': "Une raison de rejet est obligatoire."
            })
        
        if data.get('status') == 'approved':
            data['approved_at'] = timezone.now()
        
        return data


# ============================================================================
# Favorite Serializers
# ============================================================================

class FavoriteListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des favoris"""
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_city = serializers.CharField(source='listing.city', read_only=True)
    listing_daily_price = serializers.DecimalField(
        source='listing.daily_price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    listing_cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Favorite
        fields = [
            'id', 'listing', 'listing_title', 'listing_city',
            'listing_daily_price', 'listing_cover_image', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_listing_cover_image(self, obj):
        cover = obj.listing.media.filter(is_cover=True).first()
        if cover and cover.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(cover.file.url)
        return None


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """Serializer pour ajouter un favori"""
    
    class Meta:
        model = Favorite
        fields = ['listing']
    
    def validate_listing(self, value):
        """Vérifier que l'annonce existe et est publiée"""
        if value.status != 'published':
            raise serializers.ValidationError(
                "Cette annonce n'est pas disponible."
            )
        return value
    
    def validate(self, data):
        """Vérifier qu'un utilisateur ne peut pas ajouter deux fois le même favori"""
        request = self.context.get('request')
        listing = data.get('listing')
        
        if request and listing:
            existing = Favorite.objects.filter(
                user=request.user,
                listing=listing
            ).exists()
            
            if existing:
                raise serializers.ValidationError(
                    "Cette annonce est déjà dans vos favoris."
                )
        
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ============================================================================
# Statistics Serializers
# ============================================================================

class ListingReviewStatsSerializer(serializers.Serializer):
    """Statistiques des avis pour une annonce"""
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()
    rating_distribution = serializers.DictField()
    recent_reviews = ReviewListSerializer(many=True)