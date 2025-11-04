from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
import string
from .models import OTPToken, UserSession

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription"""
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password', 
                  'user_type', 'phone_number', 'profile_name']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'user_type': {'required': True},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value.lower()
    
    def validate_user_type(self, value):
        if value not in ['proprietaire', 'locataire']:
            raise serializers.ValidationError("Type d'utilisateur invalide.")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Les mots de passe ne correspondent pas."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            user_type=validated_data['user_type'],
            phone_number=validated_data.get('phone_number'),
            profile_name=validated_data.get('profile_name'),
            password=validated_data['password'],
            is_active=False  # Sera activé après vérification OTP
        )
        return user


class SendOTPSerializer(serializers.Serializer):
    """Serializer pour envoyer un OTP"""
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(choices=['login', 'register'], required=True)
    
    def validate_email(self, value):
        return value.lower()
    
    def create_otp(self, user):
        # Générer un code OTP à 6 chiffres
        token = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=10)
        
        # Invalider les anciens OTP non utilisés
        OTPToken.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Créer le nouveau OTP
        otp = OTPToken.objects.create(
            user=user,
            token=token,
            purpose=self.validated_data['purpose'],
            expires_at=expires_at
        )
        return otp


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer pour vérifier un OTP"""
    email = serializers.EmailField(required=True)
    token = serializers.CharField(required=True, max_length=6)
    device_name = serializers.CharField(required=False, default="Unknown Device")
    device_type = serializers.ChoiceField(choices=['mobile', 'desktop', 'tablet'], required=False, default='desktop')
    
    def validate(self, attrs):
        email = attrs['email'].lower()
        token = attrs['token']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Utilisateur non trouvé."})
        
        # Vérifier l'OTP
        otp = OTPToken.objects.filter(
            user=user,
            token=token,
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp:
            raise serializers.ValidationError({"token": "Code OTP invalide."})
        
        if not otp.is_valid():
            raise serializers.ValidationError({"token": "Code OTP expiré."})
        
        attrs['user'] = user
        attrs['otp'] = otp
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'user_type', 
                  'phone_number', 'profile_name', 'is_identity_verified', 
                  'identity_verified_at', 'email_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'email', 'user_type', 'is_identity_verified', 
                           'identity_verified_at', 'email_verified', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UploadIdentitySerializer(serializers.Serializer):
    """Serializer pour upload de CNI"""
    identity_document = serializers.FileField(required=True)
    
    def validate_identity_document(self, value):
        # Vérifier le type de fichier
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Format de fichier non autorisé. Utilisez JPG, PNG ou PDF.")
        
        # Vérifier la taille (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 5MB.")
        
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer pour les sessions utilisateur"""
    is_current = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = ['id', 'device_name', 'device_type', 'ip_address', 
                  'is_active', 'last_activity', 'created_at', 'is_current']
        read_only_fields = ['id', 'ip_address', 'is_active', 'last_activity', 'created_at']
    
    def get_is_current(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        current_token = request.auth
        return obj.refresh_token == str(current_token) if current_token else False


# ADMIN SERIALIZERS

class AdminUserListSerializer(serializers.ModelSerializer):
    """Serializer pour liste utilisateurs (admin)"""
    full_name = serializers.SerializerMethodField()
    sessions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'user_type',
                  'phone_number', 'profile_name', 'is_identity_verified', 'is_active',
                  'identity_verified_at', 'email_verified', 'sessions_count', 
                  'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_sessions_count(self, obj):
        return obj.sessions.filter(is_active=True).count()


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un utilisateur (admin)"""
    full_name = serializers.SerializerMethodField()
    sessions = UserSessionSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 
                  'user_type', 'phone_number', 'profile_name', 'is_identity_verified',
                  'identity_document', 'identity_verified_at', 'email_verified', 
                  'is_active', 'is_staff', 'date_joined', 'created_at', 'updated_at', 'sessions']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class VerifyIdentitySerializer(serializers.Serializer):
    """Serializer pour valider l'identité (admin)"""
    approved = serializers.BooleanField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class BlockUserSerializer(serializers.Serializer):
    """Serializer pour bloquer/débloquer un utilisateur (admin)"""
    is_active = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)