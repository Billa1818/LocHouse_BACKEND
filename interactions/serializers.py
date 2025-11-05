# ============================================================================
# interactions/serializers.py
# ============================================================================
from rest_framework import serializers
from django.utils import timezone
from .models import AvailabilityRequest, ContactMessage, Review, Favorite
from accounts.models import User
from listings.models import Listing
from core.models import Notification


# ============================================================================
# USER SERIALIZERS (pour relations)
# ============================================================================
class UserBasicSerializer(serializers.ModelSerializer):
    """Informations basiques d'un utilisateur"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'profile_name', 'user_type']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class OwnerContactSerializer(serializers.ModelSerializer):
    """Contact du propriétaire (révélé après premier message)"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone_number', 'profile_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


# ============================================================================
# LISTING SERIALIZERS (pour relations)
# ============================================================================
class ListingBasicSerializer(serializers.ModelSerializer):
    """Informations basiques d'une annonce"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'property_name', 'category', 
            'city', 'district', 'daily_price', 'monthly_price',
            'owner_name', 'cover_image'
        ]
    
    def get_cover_image(self, obj):
        cover = obj.media.filter(is_cover=True).first()
        if cover and cover.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(cover.file.url)
        return None


# ============================================================================
# AVAILABILITY REQUEST SERIALIZERS
# ============================================================================
class AvailabilityRequestSerializer(serializers.ModelSerializer):
    """Serializer pour les demandes de disponibilité"""
    listing_details = ListingBasicSerializer(source='listing', read_only=True)
    requester_details = UserBasicSerializer(source='requester', read_only=True)
    
    class Meta:
        model = AvailabilityRequest
        fields = [
            'id', 'listing', 'listing_details', 'requester', 'requester_details',
            'requester_phone', 'message', 'check_in_date', 'check_out_date',
            'guests_count', 'status', 'owner_notified', 'created_at'
        ]
        read_only_fields = ['requester', 'owner_notified', 'created_at']
    
    def validate(self, data):
        """Validation des dates"""
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        
        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError({
                    'check_out_date': 'La date de départ doit être après la date d\'arrivée'
                })
            
            if check_in < timezone.now().date():
                raise serializers.ValidationError({
                    'check_in_date': 'La date d\'arrivée ne peut pas être dans le passé'
                })
        
        # Validation du listing
        listing = data.get('listing')
        if listing and listing.status != 'published':
            raise serializers.ValidationError({
                'listing': 'Cette annonce n\'est pas disponible'
            })
        
        return data
    
    def create(self, validated_data):
        """Création avec notification conditionnelle"""
        request_obj = super().create(validated_data)
        
        # Vérifier si les notifications sont activées pour ce groupe
        if request_obj.listing.are_notifications_enabled():
            # Créer une notification pour le propriétaire
            Notification.objects.create(
                user=request_obj.listing.owner,
                notification_type='new_availability_request',
                title='Nouvelle demande de disponibilité',
                message=f"Demande pour {request_obj.listing.title}",
                link=f"/dashboard/requests/{request_obj.id}"
            )
            request_obj.owner_notified = True
            request_obj.save(update_fields=['owner_notified'])
        
        return request_obj


class AvailabilityRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mise à jour du statut (propriétaire uniquement)"""
    
    class Meta:
        model = AvailabilityRequest
        fields = ['status']
    
    def validate_status(self, value):
        """Seuls certains changements de statut sont autorisés"""
        if self.instance.status == 'closed':
            raise serializers.ValidationError("Une demande clôturée ne peut pas être modifiée")
        return value


# ============================================================================
# CONTACT MESSAGE SERIALIZERS
# ============================================================================
class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer pour les messages de contact"""
    sender_details = UserBasicSerializer(source='sender', read_only=True)
    receiver_details = UserBasicSerializer(source='receiver', read_only=True)
    listing_details = ListingBasicSerializer(source='listing', read_only=True)
    owner_contact = serializers.SerializerMethodField()
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'listing', 'listing_details', 'sender', 'sender_details',
            'receiver', 'receiver_details', 'message', 'is_first_contact',
            'is_read', 'owner_contact', 'created_at'
        ]
        read_only_fields = ['sender', 'receiver', 'is_first_contact', 'is_read', 'created_at']
    
    def get_owner_contact(self, obj):
        """Révéler le contact du propriétaire seulement après le premier message"""
        request_user = self.context.get('request').user if self.context.get('request') else None
        
        # Si c'est le locataire qui consulte et qu'il a déjà envoyé un message
        if request_user and request_user == obj.sender:
            # Vérifier s'il y a eu au moins un message de ce locataire pour ce listing
            has_sent_message = ContactMessage.objects.filter(
                listing=obj.listing,
                sender=request_user,
                is_first_contact=True
            ).exists()
            
            if has_sent_message:
                return OwnerContactSerializer(obj.listing.owner).data
        
        # Si c'est le propriétaire qui consulte
        if request_user and request_user == obj.listing.owner:
            return OwnerContactSerializer(obj.sender).data
        
        return None
    
    def validate(self, data):
        """Validation du message"""
        listing = data.get('listing')
        
        if listing and listing.status != 'published':
            raise serializers.ValidationError({
                'listing': 'Cette annonce n\'est pas disponible'
            })
        
        # Un propriétaire ne peut pas s'envoyer de message à lui-même
        request = self.context.get('request')
        if request and listing and request.user == listing.owner:
            raise serializers.ValidationError({
                'listing': 'Vous ne pouvez pas contacter votre propre annonce'
            })
        
        return data
    
    def create(self, validated_data):
        """Création avec gestion du premier contact"""
        request = self.context.get('request')
        listing = validated_data['listing']
        
        # Définir sender et receiver
        validated_data['sender'] = request.user
        validated_data['receiver'] = listing.owner
        
        # Vérifier si c'est le premier contact de ce locataire pour ce listing
        is_first = not ContactMessage.objects.filter(
            listing=listing,
            sender=request.user
        ).exists()
        
        validated_data['is_first_contact'] = is_first
        
        message_obj = super().create(validated_data)
        
        # Notification conditionnelle au propriétaire
        if listing.are_notifications_enabled():
            notification_message = 'Premier message' if is_first else 'Nouveau message'
            Notification.objects.create(
                user=listing.owner,
                notification_type='new_message',
                title=notification_message,
                message=f"Message concernant {listing.title}",
                link=f"/dashboard/messages/{message_obj.id}"
            )
        
        return message_obj


class ContactMessageListSerializer(serializers.ModelSerializer):
    """Version simplifiée pour liste de messages"""
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.get_full_name', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'listing', 'listing_title', 'sender', 'sender_name',
            'receiver', 'receiver_name', 'message_preview', 'is_read',
            'created_at'
        ]
    
    def get_message_preview(self, obj):
        """Aperçu du message (100 premiers caractères)"""
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message


# ============================================================================
# REVIEW SERIALIZERS
# ============================================================================
class ReviewSerializer(serializers.ModelSerializer):
    """Serializer pour les avis"""
    author_details = UserBasicSerializer(source='author', read_only=True)
    listing_details = ListingBasicSerializer(source='listing', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'listing', 'listing_details', 'author', 'author_details',
            'rating', 'comment', 'status', 'rejection_reason',
            'created_at', 'approved_at'
        ]
        read_only_fields = ['author', 'status', 'rejection_reason', 'created_at', 'approved_at']
    
    def validate_rating(self, value):
        """Validation de la note"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("La note doit être entre 1 et 5")
        return value
    
    def validate(self, data):
        """Validation de l'avis"""
        listing = data.get('listing')
        request = self.context.get('request')
        
        if listing and listing.status != 'published':
            raise serializers.ValidationError({
                'listing': 'Vous ne pouvez pas laisser d\'avis sur cette annonce'
            })
        
        # Un propriétaire ne peut pas laisser d'avis sur sa propre annonce
        if request and listing and request.user == listing.owner:
            raise serializers.ValidationError({
                'listing': 'Vous ne pouvez pas laisser d\'avis sur votre propre annonce'
            })
        
        # Vérifier si l'utilisateur a déjà laissé un avis (en UPDATE, exclure l'instance actuelle)
        if request and listing:
            existing_review = Review.objects.filter(
                listing=listing,
                author=request.user
            )
            if self.instance:
                existing_review = existing_review.exclude(id=self.instance.id)
            
            if existing_review.exists():
                raise serializers.ValidationError({
                    'listing': 'Vous avez déjà laissé un avis sur cette annonce'
                })
        
        return data
    
    def create(self, validated_data):
        """Création avec notification au propriétaire"""
        request = self.context.get('request')
        validated_data['author'] = request.user
        validated_data['status'] = 'pending'  # Toujours en attente de modération
        
        review_obj = super().create(validated_data)
        
        # Notification au propriétaire (même si notifications désactivées pour avis)
        Notification.objects.create(
            user=review_obj.listing.owner,
            notification_type='new_review',
            title='Nouvel avis en attente de modération',
            message=f"Avis sur {review_obj.listing.title}",
            link=f"/dashboard/reviews/{review_obj.id}"
        )
        
        return review_obj


class ReviewModerationSerializer(serializers.ModelSerializer):
    """Serializer pour modération des avis (admin uniquement)"""
    
    class Meta:
        model = Review
        fields = ['status', 'rejection_reason']
    
    def validate(self, data):
        """Validation de la modération"""
        status = data.get('status')
        rejection_reason = data.get('rejection_reason')
        
        if status == 'rejected' and not rejection_reason:
            raise serializers.ValidationError({
                'rejection_reason': 'Une raison de rejet est requise'
            })
        
        return data
    
    def update(self, instance, validated_data):
        """Mise à jour avec notification à l'auteur"""
        status = validated_data.get('status')
        
        if status == 'approved':
            validated_data['approved_at'] = timezone.now()
            notification_type = 'listing_approved'
            notification_title = 'Avis approuvé'
        elif status == 'rejected':
            notification_type = 'listing_rejected'
            notification_title = 'Avis rejeté'
        else:
            notification_type = None
            notification_title = None
        
        review_obj = super().update(instance, validated_data)
        
        # Notification à l'auteur de l'avis
        if notification_type:
            Notification.objects.create(
                user=review_obj.author,
                notification_type=notification_type,
                title=notification_title,
                message=f"Concernant votre avis sur {review_obj.listing.title}",
                link=f"/listings/{review_obj.listing.id}"
            )
        
        return review_obj


# ============================================================================
# FAVORITE SERIALIZERS
# ============================================================================
class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer pour les favoris"""
    listing_details = ListingBasicSerializer(source='listing', read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'listing', 'listing_details', 'created_at']
        read_only_fields = ['created_at']
    
    def validate_listing(self, value):
        """Validation du listing"""
        if value.status != 'published':
            raise serializers.ValidationError("Cette annonce n'est pas disponible")
        return value
    
    def create(self, validated_data):
        """Création avec gestion des doublons"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        
        # Vérifier si déjà en favoris
        existing = Favorite.objects.filter(
            user=request.user,
            listing=validated_data['listing']
        ).first()
        
        if existing:
            return existing  # Retourner le favori existant
        
        return super().create(validated_data)