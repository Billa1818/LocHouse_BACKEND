# ============================================================================
# ENDPOINTS - listings
# ============================================================================

"""
# PROPRIÉTAIRE
POST   /api/listings/                         - Créer annonce (draft)
GET    /api/listings/my-listings/             - Mes annonces
GET    /api/listings/{id}/                    - Détail annonce
PATCH  /api/listings/{id}/                    - Modifier annonce
DELETE /api/listings/{id}/                    - Supprimer annonce
POST   /api/listings/{id}/submit/             - Soumettre pour validation
POST   /api/listings/{id}/media/              - Upload médias
DELETE /api/listings/{id}/media/{media_id}/   - Supprimer média

# PUBLIC (Locataires)
GET    /api/listings/search/                  - Recherche avec filtres
GET    /api/listings/{id}/public/             - Détail public annonce
GET    /api/listings/featured/                - Annonces en vedette

# ADMIN
GET    /api/admin/listings/pending/           - Annonces en attente
PATCH  /api/admin/listings/{id}/approve/      - Approuver annonce
PATCH  /api/admin/listings/{id}/reject/       - Rejeter annonce

# ÉQUIPEMENTS
GET    /api/amenities/                        - Liste équipements disponibles
"""

"""
# ============================================================================
# DOCUMENTATION DES ENDPOINTS
# ============================================================================

"""
PROPERTY GROUPS ENDPOINTS:
--------------------------
GET     /api/listings/property-groups/                    - Liste des groupes du propriétaire connecté
POST    /api/listings/property-groups/                    - Créer un nouveau groupe
GET     /api/listings/property-groups/{id}/               - Détails d'un groupe
PUT     /api/listings/property-groups/{id}/               - Modifier un groupe
PATCH   /api/listings/property-groups/{id}/               - Modifier partiellement un groupe
DELETE  /api/listings/property-groups/{id}/               - Supprimer un groupe
POST    /api/listings/property-groups/{id}/toggle_notifications/ - Activer/désactiver les notifications
GET     /api/listings/property-groups/{id}/listings/      - Annonces d'un groupe
GET     /api/listings/property-groups/{id}/statistics/    - Statistiques d'un groupe


LISTINGS ENDPOINTS:
-------------------
GET     /api/listings/listings/                           - Liste des annonces publiées (public)
POST    /api/listings/listings/                           - Créer une nouvelle annonce (propriétaire)
GET     /api/listings/listings/{id}/                      - Détails d'une annonce
PUT     /api/listings/listings/{id}/                      - Modifier une annonce (propriétaire)
PATCH   /api/listings/listings/{id}/                      - Modifier partiellement une annonce
DELETE  /api/listings/listings/{id}/                      - Supprimer une annonce (propriétaire)

GET     /api/listings/listings/my_listings/               - Mes annonces (propriétaire)
GET     /api/listings/listings/my_dashboard/              - Dashboard propriétaire
POST    /api/listings/listings/{id}/update_status/        - Valider/rejeter annonce (admin)
GET     /api/listings/listings/pending_listings/          - Annonces en attente (admin)
POST    /api/listings/listings/{id}/add_to_favorites/     - Ajouter aux favoris
DELETE  /api/listings/listings/{id}/delete_media/         - Supprimer un média


AMENITIES ENDPOINTS:
--------------------
GET     /api/listings/amenities/                          - Liste des équipements disponibles
GET     /api/listings/amenities/{id}/                     - Détails d'un équipement


FILTRES DISPONIBLES (Query Parameters):
---------------------------------------
Pour les annonces (/api/listings/listings/):
- city: Filtrer par ville (icontains)
- district: Filtrer par quartier (icontains)
- category: residentiel ou touristique
- min_daily_price / max_daily_price: Fourchette de prix journalier
- min_monthly_price / max_monthly_price: Fourchette de prix mensuel
- min_bedrooms / max_bedrooms: Nombre de chambres
- min_bathrooms: Nombre minimum de salles de bain
- min_area: Surface minimale
- property_group: ID du groupe de propriétés
- owner: ID du propriétaire
- status: draft, pending, published, rejected, archived (admin/propriétaire)
- search: Recherche textuelle (titre, description, ville, quartier, nom propriété)
- ordering: Tri (-created_at, -published_at, daily_price, monthly_price, views_count)


EXEMPLES D'UTILISATION:
-----------------------

1. Rechercher des appartements à Cotonou avec 2+ chambres:
   GET /api/listings/listings/?city=Cotonou&min_bedrooms=2

2. Annonces touristiques avec prix journalier < 50000 FCFA:
   GET /api/listings/listings/?category=touristique&max_daily_price=50000

3. Annonces d'un groupe spécifique:
   GET /api/listings/listings/?property_group=5

4. Dashboard propriétaire avec statistiques:
   GET /api/listings/listings/my_dashboard/

5. Activer/désactiver notifications d'un groupe:
   POST /api/listings/property-groups/3/toggle_notifications/

6. Valider une annonce (admin):
   POST /api/listings/listings/42/update_status/
   Body: {"status": "published"}

7. Rejeter une annonce (admin):
   POST /api/listings/listings/42/update_status/
   Body: {"status": "rejected", "rejection_reason": "Photos de mauvaise qualité"}
"""