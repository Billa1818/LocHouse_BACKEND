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
        # L'objet doit avoir un attribut 'user' ou 'owner'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class IsRequestOwnerOrListingOwner(permissions.BasePermission):
    """
    Permission pour les demandes de disponibilité:
    - Le demandeur peut voir sa demande
    - Le propriétaire de l'annonce peut voir les demandes
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin a tous les droits
        if request.user.is_staff:
            return True
        
        # Le demandeur peut voir/modifier sa demande
        if obj.requester == request.user:
            return True
        
        # Le propriétaire de l'annonce peut voir/modifier les demandes
        if obj.listing.owner == request.user:
            return True
        
        return False


class IsReviewAuthor(permissions.BasePermission):
    """
    Permission pour les avis:
    - Seul l'auteur peut modifier/supprimer son avis
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin a tous les droits
        if request.user.is_staff:
            return True
        
        # L'auteur peut modifier/supprimer son avis
        return obj.author == request.user


class IsMessageParticipant(permissions.BasePermission):
    """
    Permission pour les messages:
    - Seuls l'expéditeur et le destinataire peuvent voir le message
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin a tous les droits
        if request.user.is_staff:
            return True
        
        # L'expéditeur ou le destinataire peut voir le message
        return obj.sender == request.user or obj.receiver == request.user


class IsAdmin(permissions.BasePermission):
    """
    Permission personnalisée:
    Seuls les administrateurs peuvent accéder
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_staff