""
============================================================================
DOCUMENTATION DES ENDPOINTS
============================================================================

# -------------------------------------------------------------------------
# AVAILABILITY REQUESTS (Demandes de disponibilité)
# -------------------------------------------------------------------------

## Endpoints de base (CRUD)
GET     /api/availability-requests/                    - Liste des demandes (filtrées selon user)
POST    /api/availability-requests/                    - Créer une demande (locataire)
GET     /api/availability-requests/{id}/               - Détail d'une demande
PUT     /api/availability-requests/{id}/               - Modifier une demande (propriétaire du request)
DELETE  /api/availability-requests/{id}/               - Supprimer une demande

## Endpoints personnalisés
GET     /api/availability-requests/my_requests/        - Mes demandes (locataire)
GET     /api/availability-requests/received_requests/  - Demandes reçues (propriétaire)
PATCH   /api/availability-requests/{id}/update_status/ - Changer statut (propriétaire du listing)

## Exemples de requêtes

### Créer une demande de disponibilité
POST /api/availability-requests/
{
    "listing": 123,
    "requester_phone": "+229 97 00 00 00",
    "message": "Bonjour, je suis intéressé par cette chambre...",
    "check_in_date": "2025-12-01",
    "check_out_date": "2025-12-05",
    "guests_count": 2
}

### Mettre à jour le statut (propriétaire)
PATCH /api/availability-requests/45/update_status/
{
    "status": "contacted"  # ou "closed"
}

### Filtrer les demandes
GET /api/availability-requests/?status=pending&listing=123


# -------------------------------------------------------------------------
# CONTACT MESSAGES (Messages de contact)
# -------------------------------------------------------------------------

## Endpoints de base (CRUD)
GET     /api/messages/                                  - Liste des messages
POST    /api/messages/                                  - Envoyer un message
GET     /api/messages/{id}/                             - Détail d'un message
DELETE  /api/messages/{id}/                             - Supprimer un message

## Endpoints personnalisés
GET     /api/messages/conversations/                    - Liste des conversations groupées
GET     /api/messages/conversation_detail/              - Détail d'une conversation (+ listing_id)
PATCH   /api/messages/{id}/mark_as_read/                - Marquer comme lu
GET     /api/messages/unread_count/                     - Nombre de messages non lus

## Exemples de requêtes

### Envoyer un message
POST /api/messages/
{
    "listing": 123,
    "message": "Bonjour, est-ce que la chambre est disponible du 1er au 5 décembre?"
}
Réponse : Si c'est le premier message, le contact du propriétaire sera révélé dans "owner_contact"

### Voir une conversation
GET /api/messages/conversation_detail/?listing_id=123

### Nombre de messages non lus
GET /api/messages/unread_count/
Réponse : {"unread_count": 5}


# -------------------------------------------------------------------------
# REVIEWS (Avis et commentaires)
# -------------------------------------------------------------------------

## Endpoints de base (CRUD)
GET     /api/reviews/                                   - Liste des avis (approuvés pour public)
POST    /api/reviews/                                   - Créer un avis (locataire)
GET     /api/reviews/{id}/                              - Détail d'un avis
PUT     /api/reviews/{id}/                              - Modifier un avis (auteur)
DELETE  /api/reviews/{id}/                              - Supprimer un avis

## Endpoints personnalisés
GET     /api/reviews/my_reviews/                        - Mes avis
GET     /api/reviews/listing_stats/                     - Statistiques d'un listing (+ listing_id)
GET     /api/reviews/pending_reviews/                   - Avis en attente (admin)
PATCH   /api/reviews/{id}/moderate/                     - Modérer un avis (admin)

## Exemples de requêtes

### Créer un avis
POST /api/reviews/
{
    "listing": 123,
    "rating": 5,
    "comment": "Excellent séjour, très propre et bien situé!"
}
Note : L'avis sera en statut "pending" jusqu'à validation admin

### Modérer un avis (admin)
PATCH /api/reviews/45/moderate/
{
    "status": "approved"
}
ou
{
    "status": "rejected",
    "rejection_reason": "Contenu inapproprié"
}

### Statistiques d'un listing
GET /api/reviews/listing_stats/?listing_id=123
Réponse :
{
    "average_rating": 4.5,
    "total_reviews": 10,
    "rating_distribution": {
        "rating_1": 0,
        "rating_2": 1,
        "rating_3": 2,
        "rating_4": 3,
        "rating_5": 4
    }
}

### Filtrer les avis
GET /api/reviews/?listing=123&status=approved&ordering=-created_at


# -------------------------------------------------------------------------
# FAVORITES (Favoris)
# -------------------------------------------------------------------------

## Endpoints de base
GET     /api/favorites/                                 - Liste de mes favoris
POST    /api/favorites/                                 - Ajouter un favori
DELETE  /api/favorites/{id}/                            - Retirer un favori

## Endpoints personnalisés
POST    /api/favorites/toggle/                          - Ajouter/retirer (toggle)
GET     /api/favorites/check/                           - Vérifier si en favoris (+ listing_id)

## Exemples de requêtes

### Ajouter aux favoris
POST /api/favorites/
{
    "listing": 123
}

### Toggle favori (plus pratique)
POST /api/favorites/toggle/
{
    "listing": 123
}
Réponse : {"message": "Ajouté aux favoris", "is_favorite": true}
ou {"message": "Retiré des favoris", "is_favorite": false}

### Vérifier si un listing est en favoris
GET /api/favorites/check/?listing_id=123
Réponse : {"is_favorite": true}


# -------------------------------------------------------------------------
# FILTRES ET RECHERCHE
# -------------------------------------------------------------------------

## Filtres disponibles pour tous les endpoints

### AvailabilityRequests
- status : pending, contacted, closed
- listing : ID du listing
- ordering : created_at, check_in_date (avec - pour décroissant)
- search : recherche dans message et listing__title

### Messages
- listing : ID du listing
- is_read : true/false
- ordering : created_at

### Reviews
- listing : ID du listing
- status : pending, approved, rejected
- rating : 1-5
- ordering : created_at, rating

### Favorites
- Pas de filtres (toujours les favoris de l'utilisateur)

## Exemples de requêtes avec filtres
GET /api/availability-requests/?status=pending&ordering=-created_at
GET /api/reviews/?listing=123&status=approved&rating=5
GET /api/messages/?is_read=false


# -------------------------------------------------------------------------
# PERMISSIONS ET SÉCURITÉ
# -------------------------------------------------------------------------

## Règles de permissions

### AvailabilityRequests
- Locataires : peuvent créer et voir leurs demandes
- Propriétaires : peuvent voir les demandes pour leurs listings et changer le statut
- Admin : accès complet

### Messages
- Locataires et Propriétaires : peuvent envoyer/recevoir des messages
- Chaque user voit uniquement les messages où il est sender ou receiver
- Le contact du propriétaire est révélé après le premier message

### Reviews
- Public : peut voir les avis approuvés (sans authentification)
- Locataires : peuvent créer et voir leurs avis
- Propriétaires : peuvent voir les avis approuvés + avis sur leurs listings
- Admin : peuvent modérer tous les avis

### Favorites
- Utilisateurs authentifiés uniquement
- Chaque user voit uniquement ses propres favoris

## Notifications
- Respecte PropertyGroup.notifications_enabled
- Si désactivé, aucune notification n'est envoyée pour ce groupe
- Exceptions : notifications critiques (admin) toujours envoyées


# -------------------------------------------------------------------------
# CODES DE STATUT HTTP
# -------------------------------------------------------------------------

200 OK                  - Requête réussie
201 Created             - Ressource créée avec succès
204 No Content          - Suppression réussie
400 Bad Request         - Données invalides
401 Unauthorized        - Authentication requise
403 Forbidden           - Permissions insuffisantes
404 Not Found           - Ressource non trouvée
500 Internal Error      - Erreur serveur


# -------------------------------------------------------------------------
# PAGINATION
# -------------------------------------------------------------------------

Toutes les listes sont paginées par défaut.
Format de réponse :
{
    "count": 100,
    "next": "http://api.example.com/api/reviews/?page=2",
    "previous": null,
    "results": [...]
}

Paramètres :
- page : numéro de page (défaut: 1)
- page_size : nombre d'éléments par page (max: 100)

Exemple : GET /api/reviews/?page=2&page_size=20
"""