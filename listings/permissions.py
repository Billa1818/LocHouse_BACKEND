from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée: 
    - Lecture autorisée pour tous
    - Modification/suppression uniquement pour le propriétaire
    """
    
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture uniquement pour le propriétaire
        return obj.owner == request.user


class IsOwner(permissions.BasePermission):
    """
    Permission personnalisée:
    Seul le propriétaire peut accéder à l'objet
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


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
        return request.user and request.user.is_authenticated and request.user.user_type == 'proprietaire'