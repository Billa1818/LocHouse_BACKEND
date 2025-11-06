from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import OTPToken, UserSession
from django.contrib.admin import AdminSite

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personnalisé pour le modèle User"""
    
    list_display = ['email', 'full_name', 'user_type', 'is_identity_verified', 
                    'email_verified', 'is_active', 'is_staff', 'created_at']
    list_filter = ['user_type', 'is_identity_verified', 'email_verified', 
                   'is_active', 'is_staff', 'is_superuser']
    search_fields = ['email', 'first_name', 'last_name', 'profile_name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('email', 'username', 'first_name', 'last_name')
        }),
        ('Informations profil', {
            'fields': ('user_type', 'phone_number', 'profile_name')
        }),
        ('Vérification', {
            'fields': ('email_verified', 'is_identity_verified', 
                      'identity_document', 'identity_verified_at')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 
                      'groups', 'user_permissions')
        }),
        ('Dates', {
            'fields': ('date_joined', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['date_joined', 'created_at', 'updated_at', 'identity_verified_at']
    
    add_fieldsets = (
        ('Informations requises', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type'),
        }),
        ('Informations optionnelles', {
            'fields': ('phone_number', 'profile_name'),
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser'),
        }),
    )
    
    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Nom complet'
    
    def save_model(self, request, obj, form, change):
        """Sauvegarder sans mot de passe"""
        if not change:  # Création
            obj.username = obj.email
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)


@admin.register(OTPToken)
class OTPTokenAdmin(admin.ModelAdmin):
    """Admin pour les tokens OTP"""
    
    list_display = ['user', 'token', 'purpose', 'is_used', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_used', 'created_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['user', 'token', 'purpose', 'expires_at', 'is_used', 'created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin pour les sessions utilisateur"""
    
    list_display = ['user', 'device_name', 'device_type', 'ip_address', 
                    'is_active', 'last_activity', 'created_at']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__email', 'device_name', 'ip_address']
    readonly_fields = ['user', 'device_name', 'device_type', 'ip_address', 
                      'user_agent', 'refresh_token', 'last_activity', 'created_at']
    ordering = ['-last_activity']
    
    def has_add_permission(self, request):
        return False



class OTPAdminSite(AdminSite):
    login_template = 'admin/otp_login.html'
    
    def login(self, request, extra_context=None):
        """
        Rediriger vers notre vue personnalisée
        """
        from django.shortcuts import redirect
        return redirect('admin:otp_login')