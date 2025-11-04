
"""
=============================================================================
DOCUMENTATION DES ROUTES API - APP CORE
=============================================================================

PAGES STATIQUES (Public pour list/retrieve, Admin pour CUD - EF-A-07):
-----------------------------------------------------------------------------
GET    /api/core/static-pages/                    
    - Liste toutes les pages statiques publiées
    - Permissions: AllowAny
    - Retourne: Liste de pages (titre, slug, meta_description)

POST   /api/core/static-pages/                    
    - Créer une nouvelle page statique
    - Permissions: IsAdminUser
    - Body: {slug, title, content, meta_description?, is_published?}

GET    /api/core/static-pages/{slug}/             
    - Détail d'une page statique spécifique
    - Permissions: AllowAny
    - Retourne: Page complète avec contenu

PUT    /api/core/static-pages/{slug}/             
    - Modifier complètement une page
    - Permissions: IsAdminUser
    - Body: {title, content, meta_description?, is_published?}

PATCH  /api/core/static-pages/{slug}/             
    - Modifier partiellement une page
    - Permissions: IsAdminUser
    - Body: Champs à modifier seulement

DELETE /api/core/static-pages/{slug}/             
    - Supprimer une page statique
    - Permissions: IsAdminUser


NOTIFICATIONS (Authentifié uniquement):
-----------------------------------------------------------------------------
GET    /api/core/notifications/                   
    - Liste toutes les notifications de l'utilisateur connecté
    - Permissions: IsAuthenticated
    - Query params: ?is_read=true/false (optionnel)
    - Retourne: Liste des notifications avec pagination

GET    /api/core/notifications/{id}/              
    - Détail d'une notification spécifique
    - Permissions: IsAuthenticated (propriétaire uniquement)
    - Retourne: Notification complète

GET    /api/core/notifications/unread_count/      
    - Nombre de notifications non lues
    - Permissions: IsAuthenticated
    - Retourne: {unread_count: number}

POST   /api/core/notifications/{id}/mark_read/    
    - Marquer une notification comme lue
    - Permissions: IsAuthenticated (propriétaire uniquement)
    - Retourne: Notification mise à jour

POST   /api/core/notifications/mark_multiple_read/ 
    - Marquer plusieurs notifications comme lues
    - Permissions: IsAuthenticated
    - Body option 1: {notification_ids: [1, 2, 3]}
    - Body option 2: {mark_all: true}
    - Retourne: {message: string, updated_count: number}

DELETE /api/core/notifications/delete_all_read/   
    - Supprimer toutes les notifications déjà lues
    - Permissions: IsAuthenticated
    - Retourne: {message: string, deleted_count: number}


ANALYTICS (Admin uniquement - EF-A-08):
-----------------------------------------------------------------------------
GET    /api/core/analytics/                       
    - Liste des statistiques quotidiennes
    - Permissions: IsAdminUser
    - Query params: ?date__gte=YYYY-MM-DD&date__lte=YYYY-MM-DD
    - Retourne: Liste des analytics avec pagination

POST   /api/core/analytics/                       
    - Créer une entrée de statistiques
    - Permissions: IsAdminUser
    - Body: {date, new_users, new_listings, active_subscriptions, revenue, total_searches, total_contacts}

GET    /api/core/analytics/{id}/                  
    - Détail des stats d'un jour spécifique
    - Permissions: IsAdminUser

PUT    /api/core/analytics/{id}/                  
    - Modifier les statistiques d'un jour
    - Permissions: IsAdminUser

DELETE /api/core/analytics/{id}/                  
    - Supprimer une entrée de statistiques
    - Permissions: IsAdminUser

GET    /api/core/analytics/summary/               
    - Résumé agrégé des statistiques sur une période
    - Permissions: IsAdminUser
    - Query params: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    - Par défaut: 30 derniers jours
    - Retourne: {
        total_users, total_listings, total_active_subscriptions,
        total_revenue, total_searches, total_contacts,
        period_start, period_end, daily_breakdown: [...]
      }

GET    /api/core/analytics/dashboard/             
    - Statistiques complètes du tableau de bord admin
    - Permissions: IsAdminUser
    - Retourne: {
        total_users, total_proprietaires, total_locataires,
        total_listings, published_listings, pending_listings,
        total_property_groups, active_subscriptions, expired_subscriptions,
        trial_subscriptions, total_revenue_today, total_revenue_month,
        total_revenue_year, pending_identity_verifications
      }


=============================================================================
EXEMPLES D'UTILISATION
=============================================================================

1. Récupérer les CGU (Conditions Générales d'Utilisation):
   GET /api/core/static-pages/cgu/

2. Récupérer mes notifications non lues uniquement:
   GET /api/core/notifications/?is_read=false

3. Compter mes notifications non lues:
   GET /api/core/notifications/unread_count/

4. Marquer toutes mes notifications comme lues:
   POST /api/core/notifications/mark_multiple_read/
   Body: {"mark_all": true}

5. Marquer des notifications spécifiques comme lues:
   POST /api/core/notifications/mark_multiple_read/
   Body: {"notification_ids": [1, 5, 12]}

6. Supprimer toutes mes notifications déjà lues:
   DELETE /api/core/notifications/delete_all_read/

7. Obtenir les stats des 30 derniers jours:
   GET /api/core/analytics/summary/?start_date=2025-10-01&end_date=2025-11-01

8. Obtenir les stats d'une période précise:
   GET /api/core/analytics/summary/?start_date=2025-01-01&end_date=2025-01-31

9. Dashboard admin complet avec toutes les métriques:
   GET /api/core/analytics/dashboard/

10. Créer une page statique (Admin):
    POST /api/core/static-pages/
    Body: {
        "slug": "faq",
        "title": "Questions Fréquentes",
        "content": "# FAQ\n\n...",
        "meta_description": "FAQ LocHouse",
        "is_published": true
    }


=============================================================================
CODES DE STATUT HTTP
=============================================================================
200 OK              - Requête réussie
201 Created         - Ressource créée
204 No Content      - Suppression réussie
400 Bad Request     - Données invalides
401 Unauthorized    - Non authentifié
403 Forbidden       - Pas les permissions
404 Not Found       - Ressource introuvable
500 Server Error    - Erreur serveur
"""