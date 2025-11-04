from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission: l'utilisateur doit être le propriétaire de l'objet ou un admin
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class IsProprietaire(permissions.BasePermission):
    """
    Permission: l'utilisateur doit être de type 'proprietaire'
    """
    message = "Seuls les propriétaires peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'proprietaire'
        )


class IsLocataire(permissions.BasePermission):
    """
    Permission: l'utilisateur doit être de type 'locataire'
    """
    message = "Seuls les locataires peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'locataire'
        )


class IsAdminUser(permissions.BasePermission):
    """
    Permission: l'utilisateur doit être admin
    """
    message = "Seuls les administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.user_type == 'admin')
        )


class IsIdentityVerified(permissions.BasePermission):
    """
    Permission: l'identité de l'utilisateur doit être vérifiée
    """
    message = "Votre identité doit être vérifiée pour effectuer cette action."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_identity_verified
        )


class IsEmailVerified(permissions.BasePermission):
    """
    Permission: l'email de l'utilisateur doit être vérifié
    """
    message = "Votre email doit être vérifié pour effectuer cette action."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.email_verified
        )