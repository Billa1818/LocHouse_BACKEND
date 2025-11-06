from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .tasks import (
    send_otp_email_task,
    send_identity_verification_email_task,
    send_account_status_email_task
)
from rest_framework.views import APIView
from .models import OTPToken, UserSession
from .serializers import (
    UserRegistrationSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
    UserProfileSerializer,
    UploadIdentitySerializer,
    UserSessionSerializer,
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    VerifyIdentitySerializer,
    BlockUserSerializer
)
from .permissions import IsAdminUser, IsProprietaire

User = get_user_model()


def get_client_ip(request):
    """Récupérer l'IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class RegisterView(generics.CreateAPIView):
    """Vue pour l'inscription des utilisateurs"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Vérifier si l'utilisateur existe déjà
        email = serializer.validated_data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Un compte avec cet email existe déjà.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        
        # Créer et envoyer l'OTP
        otp_serializer = SendOTPSerializer(data={
            'email': user.email,
            'purpose': 'register'
        })
        otp_serializer.is_valid(raise_exception=True)
        otp = otp_serializer.create_otp(user)
        send_otp_email_task.delay(user.id, otp.token, user.get_full_name())
        
        return Response({
            'message': 'Inscription réussie. Un code de vérification a été envoyé à votre email.',
            'email': user.email
        }, status=status.HTTP_201_CREATED)


class SendOTPView(generics.GenericAPIView):
    """Vue pour envoyer un OTP"""
    serializer_class = SendOTPSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        purpose = serializer.validated_data['purpose']
        
        try:
            # Utiliser filter().first() pour éviter l'erreur MultipleObjectsReturned
            user = User.objects.filter(email=email).first()
            
            if not user:
                return Response({
                    'error': 'Aucun compte associé à cet email.'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'error': 'Une erreur est survenue.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Créer et envoyer l'OTP
        otp = serializer.create_otp(user)
        send_otp_email_task.delay(user.id, otp.token, user.get_full_name())
        
        return Response({
            'message': f'Code de vérification envoyé à {email}.',
            'expires_in': 600  # 10 minutes en secondes
        }, status=status.HTTP_200_OK)

class VerifyOTPView(generics.GenericAPIView):
    """Vue pour vérifier un OTP et obtenir les tokens JWT"""
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        otp = serializer.validated_data['otp']
        
        # Marquer l'OTP comme utilisé
        otp.is_used = True
        otp.save()
        
        # Activer l'utilisateur et marquer l'email comme vérifié
        if not user.is_active:
            user.is_active = True
        user.email_verified = True
        user.save()
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        # Créer la session
        device_name = serializer.validated_data.get('device_name', 'Unknown Device')
        device_type = serializer.validated_data.get('device_type', 'desktop')
        
        session = UserSession.objects.create(
            user=user,
            device_name=device_name,
            device_type=device_type,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            refresh_token=str(refresh)
        )
        
        return Response({
            'message': 'Authentification réussie.',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data,
            'session_id': session.id
        }, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """Vue pour rafraîchir le token d'accès"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token requis.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            
            # Mettre à jour l'activité de la session
            UserSession.objects.filter(
                refresh_token=refresh_token
            ).update(last_activity=timezone.now())
            
            return Response({
                'access': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response({
                'error': 'Token invalide ou expiré.'
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(generics.GenericAPIView):
    """Vue pour se déconnecter"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token requis.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Invalider la session
            UserSession.objects.filter(
                user=request.user,
                refresh_token=refresh_token
            ).update(is_active=False)
            
            # Blacklister le token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Déconnexion réussie.'
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response({
                'error': 'Token invalide.'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour consulter et modifier le profil utilisateur"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UploadIdentityView(generics.GenericAPIView):
    """Vue pour uploader la CNI (propriétaires uniquement)"""
    serializer_class = UploadIdentitySerializer
    permission_classes = [IsAuthenticated, IsProprietaire]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.identity_document = serializer.validated_data['identity_document']
        user.save()
        
        return Response({
            'message': 'Document d\'identité uploadé avec succès. En attente de validation.',
            'identity_document': user.identity_document.url if user.identity_document else None
        }, status=status.HTTP_200_OK)


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour gérer les sessions utilisateur"""
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserSession.objects.filter(
            user=self.request.user,
            is_active=True
        )
    
    @action(detail=True, methods=['delete'])
    def disconnect(self, request, pk=None):
        """Déconnecter un appareil spécifique"""
        session = self.get_object()
        
        # Empêcher la déconnexion de la session actuelle
        current_refresh = request.data.get('current_refresh')
        if session.refresh_token == current_refresh:
            return Response({
                'error': 'Impossible de déconnecter la session actuelle.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Désactiver la session
        session.is_active = False
        session.save()
        
        # Blacklister le token si possible
        try:
            token = RefreshToken(session.refresh_token)
            token.blacklist()
        except:
            pass
        
        return Response({
            'message': 'Appareil déconnecté avec succès.'
        }, status=status.HTTP_200_OK)


# ============================================================================
# VUES ADMIN
# ============================================================================

class AdminUserViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion admin des utilisateurs"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AdminUserListSerializer
        return AdminUserDetailSerializer
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # Filtres
        user_type = self.request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(is_identity_verified=is_verified.lower() == 'true')
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Recherche
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(profile_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['patch'])
    def verify_identity(self, request, pk=None):
        """Valider ou rejeter l'identité d'un utilisateur"""
        user = self.get_object()
        serializer = VerifyIdentitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        approved = serializer.validated_data['approved']
        notes = serializer.validated_data.get('notes', '')
        
        if approved:
            user.is_identity_verified = True
            user.identity_verified_at = timezone.now()
            message = 'Identité validée avec succès.'
        else:
            user.is_identity_verified = False
            user.identity_verified_at = None
            user.identity_document = None
            message = 'Identité rejetée.'

        user.save()
        
        # Envoyer l'email de notification
        send_identity_verification_email_task.delay(user.id, approved, notes)
        
        return Response({
            'message': message,
            'user': AdminUserDetailSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'])
    def block(self, request, pk=None):
        """Bloquer ou débloquer un utilisateur"""
        user = self.get_object()
        serializer = BlockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        is_active = serializer.validated_data['is_active']
        reason = serializer.validated_data.get('reason', '')
        
        user.is_active = is_active
        user.save()
        
        # Déconnecter toutes les sessions si bloqué
        if not is_active:
            UserSession.objects.filter(user=user).update(is_active=False)
        
        action_text = 'débloqué' if is_active else 'bloqué'
        
        # Envoyer l'email de notification via Celery
        send_account_status_email_task.delay(user.id, is_active, reason)
        
        return Response({
            'message': f'Utilisateur {action_text} avec succès.',
            'user': AdminUserDetailSerializer(user).data
        }, status=status.HTTP_200_OK)