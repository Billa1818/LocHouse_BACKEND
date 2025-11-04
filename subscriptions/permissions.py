from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission personnalisée:
    Seul le propriétaire (user) peut accéder à l'objet
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin a tous les droits
        if request.user.is_staff:
            return True
        
        # Vérifier si l'objet a un attribut 'user'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsAdmin(permissions.BasePermission):
    """
    Permission personnalisée:
    Seuls les administrateurs peuvent accéder
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_staff


class IsPropertyOwner(permissions.BasePermission):
    """
    Permission pour vérifier que l'utilisateur est propriétaire
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'proprietaire'
        )


class CanCreateSubscription(permissions.BasePermission):
    """
    Permission pour vérifier qu'un utilisateur peut créer un abonnement
    """
    
    def has_permission(self, request, view):
        # Seuls les propriétaires peuvent créer des abonnements
        if not request.user.is_authenticated:
            return False
        
        if request.user.user_type != 'proprietaire':
            return False
        
        return True