from rest_framework import serializers
from .models import PropertyGroup, Listing, ListingAmenity, ListingAmenityRelation, ListingMedia
from accounts.models import User


# ============================================================================
# PropertyGroup Serializers
# ============================================================================

class PropertyGroupListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des groupes de propriétés"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    listings_count = serializers.IntegerField(source='listings.count', read_only=True)
    
    class Meta:
        model = PropertyGroup
        fields = [
            'id', 'name', 'description', 'notifications_enabled',
            'owner_name', 'listings_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PropertyGroupDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un groupe de propriétés"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    listings_count = serializers.IntegerField(source='listings.count', read_only=True)
    
    class Meta:
        model = PropertyGroup
        fields = [
            'id', 'owner', 'name', 'description', 'notifications_enabled',
            'owner_name', 'listings_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']


class PropertyGroupCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour création/mise à jour de groupe"""
    
    class Meta:
        model = PropertyGroup
        fields = ['id', 'name', 'description', 'notifications_enabled']
        read_only_fields = ['id']
    
    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Le nom doit contenir au moins 3 caractères.")
        return value


# ============================================================================
# Listing Serializers
# ============================================================================

class ListingMediaSerializer(serializers.ModelSerializer):
    """Serializer pour les médias (photos/vidéos)"""
    
    class Meta:
        model = ListingMedia
        fields = [
            'id', 'media_type', 'file', 'video_url', 
            'order', 'is_cover', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']


class ListingAmenitySerializer(serializers.ModelSerializer):
    """Serializer pour les équipements"""
    
    class Meta:
        model = ListingAmenity
        fields = ['id', 'name', 'icon']


class ListingListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des annonces (vue simplifiée)"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    property_group_name = serializers.CharField(source='property_group.name', read_only=True)
    cover_image = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'property_name', 'category', 'status',
            'daily_price', 'monthly_price', 'city', 'district',
            'bedrooms', 'bathrooms', 'area', 'views_count',
            'owner_name', 'property_group_name', 'cover_image',
            'amenities', 'created_at', 'published_at'
        ]
    
    def get_cover_image(self, obj):
        cover = obj.media.filter(is_cover=True).first()
        if cover and cover.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(cover.file.url)
        return None
    
    def get_amenities(self, obj):
        amenities = ListingAmenity.objects.filter(
            listingamenityrelation__listing=obj
        )
        return ListingAmenitySerializer(amenities, many=True).data


class ListingDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une annonce"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_profile_name = serializers.CharField(source='owner.profile_name', read_only=True)
    owner_email = serializers.SerializerMethodField()
    owner_phone = serializers.SerializerMethodField()
    property_group_name = serializers.CharField(source='property_group.name', read_only=True)
    property_group_id = serializers.IntegerField(source='property_group.id', read_only=True)
    media = ListingMediaSerializer(many=True, read_only=True)
    amenities = serializers.SerializerMethodField()
    notifications_enabled = serializers.BooleanField(source='are_notifications_enabled', read_only=True)
    
    class Meta:
        model = Listing
        fields = [
            'id', 'owner', 'owner_name', 'owner_profile_name', 
            'owner_email', 'owner_phone', 'property_group', 'property_group_name',
            'property_group_id', 'title', 'description', 'property_name',
            'category', 'daily_price', 'monthly_price', 'city', 'district',
            'address', 'latitude', 'longitude', 'bedrooms', 'bathrooms',
            'area', 'status', 'rejection_reason', 'views_count',
            'media', 'amenities', 'notifications_enabled',
            'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = ['owner', 'views_count', 'created_at', 'updated_at']
    
    def get_owner_email(self, obj):
        """Email du propriétaire (visible seulement après premier contact)"""
        request = self.context.get('request')
        # Logique métier: vérifier si le locataire a déjà contacté
        # Pour l'instant, on retourne None (à implémenter avec le module de contact)
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # TODO: Vérifier si l'utilisateur a déjà envoyé un message
            return None
        return None
    
    def get_owner_phone(self, obj):
        """Téléphone du propriétaire (visible seulement après premier contact)"""
        request = self.context.get('request')
        # Même logique que pour l'email
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # TODO: Vérifier si l'utilisateur a déjà envoyé un message
            return None
        return None
    
    def get_amenities(self, obj):
        amenities = ListingAmenity.objects.filter(
            listingamenityrelation__listing=obj
        )
        return ListingAmenitySerializer(amenities, many=True).data


class ListingCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour création/mise à jour d'annonce"""
    amenity_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Listing
        fields = [
            'id', 'property_group', 'title', 'description', 'property_name',
            'category', 'daily_price', 'monthly_price', 'city', 'district',
            'address', 'latitude', 'longitude', 'bedrooms', 'bathrooms',
            'area', 'amenity_ids', 'media_files'
        ]
        read_only_fields = ['id']
    
    def validate_property_group(self, value):
        """Vérifier que le groupe appartient au propriétaire"""
        request = self.context.get('request')
        if request and value and value.owner != request.user:
            raise serializers.ValidationError(
                "Ce groupe de propriétés ne vous appartient pas."
            )
        return value
    
    def validate(self, data):
        """Validations croisées"""
        # Au moins un prix doit être défini
        if not data.get('daily_price') and not data.get('monthly_price'):
            raise serializers.ValidationError(
                "Veuillez définir au moins un prix (journalier ou mensuel)."
            )
        
        # Vérifier que le titre n'est pas vide
        if len(data.get('title', '').strip()) < 10:
            raise serializers.ValidationError({
                'title': "Le titre doit contenir au moins 10 caractères."
            })
        
        # Vérifier la description
        if len(data.get('description', '').strip()) < 50:
            raise serializers.ValidationError({
                'description': "La description doit contenir au moins 50 caractères."
            })
        
        return data
    
    def create(self, validated_data):
        amenity_ids = validated_data.pop('amenity_ids', [])
        media_files = validated_data.pop('media_files', [])
        
        # Créer l'annonce avec statut "pending" (en attente de validation)
        validated_data['status'] = 'pending'
        listing = Listing.objects.create(**validated_data)
        
        # Ajouter les équipements
        if amenity_ids:
            for amenity_id in amenity_ids:
                try:
                    amenity = ListingAmenity.objects.get(id=amenity_id)
                    ListingAmenityRelation.objects.create(
                        listing=listing,
                        amenity=amenity
                    )
                except ListingAmenity.DoesNotExist:
                    pass
        
        # Ajouter les médias
        if media_files:
            for index, media_file in enumerate(media_files):
                ListingMedia.objects.create(
                    listing=listing,
                    media_type='image',
                    file=media_file,
                    order=index,
                    is_cover=(index == 0)  # Premier média = cover
                )
        
        return listing
    
    def update(self, instance, validated_data):
        amenity_ids = validated_data.pop('amenity_ids', None)
        media_files = validated_data.pop('media_files', None)
        
        # Si modification majeure, remettre en attente de validation
        major_fields = ['title', 'description', 'daily_price', 'monthly_price', 'address']
        if any(field in validated_data for field in major_fields):
            validated_data['status'] = 'pending'
        
        # Mettre à jour les champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mettre à jour les équipements
        if amenity_ids is not None:
            # Supprimer les anciennes relations
            ListingAmenityRelation.objects.filter(listing=instance).delete()
            # Créer les nouvelles
            for amenity_id in amenity_ids:
                try:
                    amenity = ListingAmenity.objects.get(id=amenity_id)
                    ListingAmenityRelation.objects.create(
                        listing=instance,
                        amenity=amenity
                    )
                except ListingAmenity.DoesNotExist:
                    pass
        
        # Ajouter de nouveaux médias (sans supprimer les existants)
        if media_files:
            max_order = instance.media.aggregate(
                models.Max('order')
            )['order__max'] or -1
            
            for index, media_file in enumerate(media_files):
                ListingMedia.objects.create(
                    listing=instance,
                    media_type='image',
                    file=media_file,
                    order=max_order + index + 1
                )
        
        return instance


class ListingStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mise à jour du statut (Admin uniquement)"""
    
    class Meta:
        model = Listing
        fields = ['status', 'rejection_reason']
    
    def validate(self, data):
        if data.get('status') == 'rejected' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': "Une raison de rejet est obligatoire."
            })
        return data
    