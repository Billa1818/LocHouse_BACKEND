
# ============================================================================
# ENDPOINTS - interactions
# ============================================================================

"""
# DEMANDES DE DISPONIBILITÉ (NOUVELLE FONCTIONNALITÉ)
POST   /api/interactions/availability-request/      - Envoyer demande disponibilité
GET    /api/interactions/my-requests/               - Mes demandes (locataire)
GET    /api/interactions/received-requests/         - Demandes reçues (propriétaire)
PATCH  /api/interactions/requests/{id}/status/      - Marquer comme contacté

# MESSAGES
POST   /api/interactions/messages/                  - Envoyer message
GET    /api/interactions/messages/{listing_id}/     - Conversation pour une annonce
GET    /api/interactions/conversations/             - Liste conversations

# AVIS
POST   /api/interactions/reviews/                   - Poster avis
GET    /api/interactions/reviews/{listing_id}/      - Avis d'une annonce
GET    /api/interactions/my-reviews/                - Mes avis

# ADMIN
GET    /api/admin/reviews/pending/                  - Avis en attente
PATCH  /api/admin/reviews/{id}/approve/             - Approuver avis
PATCH  /api/admin/reviews/{id}/reject/              - Rejeter avis

# FAVORIS
POST   /api/interactions/favorites/                 - Ajouter favori
GET    /api/interactions/favorites/                 - Mes favoris
DELETE /api/interactions/favorites/{id}/            - Retirer favori
"""

"""

"""
AVAILABILITY REQUESTS ENDPOINTS:
--------------------------------
GET     /api/interactions/availability-requests/                      - Liste des demandes (selon rôle)
POST    /api/interactions/availability-requests/                      - Créer une demande (locataire)
GET     /api/interactions/availability-requests/{id}/                 - Détails d'une demande
PUT     /api/interactions/availability-requests/{id}/                 - Modifier une demande
PATCH   /api/interactions/availability-requests/{id}/                 - Modifier partiellement
DELETE  /api/interactions/availability-requests/{id}/                 - Supprimer une demande

GET     /api/interactions/availability-requests/my_requests/          - Mes demandes (locataire)
GET     /api/interactions/availability-requests/received_requests/    - Demandes reçues (propriétaire)
POST    /api/interactions/availability-requests/{id}/update_status/   - Mettre à jour le statut


CONTACT MESSAGES ENDPOINTS:
---------------------------
GET     /api/interactions/contact-messages/                           - Liste des messages
POST    /api/interactions/contact-messages/                           - Envoyer un message
GET     /api/interactions/contact-messages/{id}/                      - Détails d'un message
DELETE  /api/interactions/contact-messages/{id}/                      - Supprimer un message

GET     /api/interactions/contact-messages/conversations/             - Liste des conversations
GET     /api/interactions/contact-messages/by_listing/                - Messages d'une conversation
GET     /api/interactions/contact-messages/unread_count/              - Nombre de non lus


REVIEWS ENDPOINTS:
------------------
GET     /api/interactions/reviews/                                    - Liste des avis (approuvés)
POST    /api/interactions/reviews/                                    - Créer un avis
GET     /api/interactions/reviews/{id}/                               - Détails d'un avis
PUT     /api/interactions/reviews/{id}/                               - Modifier un avis (auteur)
PATCH   /api/interactions/reviews/{id}/                               - Modifier partiellement
DELETE  /api/interactions/reviews/{id}/                               - Supprimer un avis (auteur)

GET     /api/interactions/reviews/my_reviews/                         - Mes avis
GET     /api/interactions/reviews/by_listing/                         - Avis d'une annonce
POST    /api/interactions/reviews/{id}/moderate/                      - Modérer un avis (admin)
GET     /api/interactions/reviews/pending_reviews/                    - Avis en attente (admin)
GET     /api/interactions/reviews/statistics/                         - Statistiques des avis


FAVORITES ENDPOINTS:
--------------------
GET     /api/interactions/favorites/                                  - Mes favoris
POST    /api/interactions/favorites/                                  - Ajouter un favori
DELETE  /api/interactions/favorites/{id}/                             - Supprimer un favori

POST    /api/interactions/favorites/toggle/                           - Ajouter/retirer (toggle)
GET     /api/interactions/favorites/check/                            - Vérifier si favori


EXEMPLES D'UTILISATION:
-----------------------

1. Créer une demande de disponibilité:
   POST /api/interactions/availability-requests/
   Body: {
       "listing": 42,
       "requester_phone": "+22961234567",
       "message": "Je suis intéressé par cette annonce...",
       "check_in_date": "2025-12-01",
       "check_out_date": "2025-12-05",
       "guests_count": 2
   }

2. Voir les demandes reçues (propriétaire):
   GET /api/interactions/availability-requests/received_requests/

3. Mettre à jour le statut d'une demande:
   POST /api/interactions/availability-requests/15/update_status/
   Body: {"status": "contacted"}

4. Envoyer un message au propriétaire:
   POST /api/interactions/contact-messages/
   Body: {
       "listing": 42,
       "receiver": 10,
       "message": "Bonjour, l'annonce est-elle toujours disponible ?"
   }

5. Voir les conversations:
   GET /api/interactions/contact-messages/conversations/

6. Voir les messages d'une conversation spécifique:
   GET /api/interactions/contact-messages/by_listing/?listing_id=42

7. Nombre de messages non lus:
   GET /api/interactions/contact-messages/unread_count/

8. Créer un avis:
   POST /api/interactions/reviews/
   Body: {
       "listing": 42,
       "rating": 5,
       "comment": "Excellent logement, très propre et bien situé..."
   }

9. Voir les avis d'une annonce avec statistiques:
   GET /api/interactions/reviews/by_listing/?listing_id=42

10. Statistiques détaillées des avis:
    GET /api/interactions/reviews/statistics/?listing_id=42

11. Modérer un avis (admin):
    POST /api/interactions/reviews/25/moderate/
    Body: {"status": "approved"}
    OU
    Body: {
        "status": "rejected",
        "rejection_reason": "Contenu inapproprié"
    }

12. Avis en attente de modération (admin):
    GET /api/interactions/reviews/pending_reviews/

13. Ajouter aux favoris:
    POST /api/interactions/favorites/
    Body: {"listing": 42}

14. Toggle favori (ajouter ou retirer):
    POST /api/interactions/favorites/toggle/
    Body: {"listing_id": 42}

15. Vérifier si une annonce est favorite:
    GET /api/interactions/favorites/check/?listing_id=42

16. Liste de mes favoris:
    GET /api/interactions/favorites/


FILTRES DISPONIBLES (Query Parameters):
---------------------------------------

Pour les demandes de disponibilité:
- status: pending, contacted, closed
- listing: ID de l'annonce
- ordering: created_at, check_in_date

Pour les messages:
- listing: ID de l'annonce
- is_read: true, false

Pour les avis:
- listing: ID de l'annonce
- rating: 1, 2, 3, 4, 5
- status: pending, approved, rejected
- ordering: created_at, rating


LOGIQUE MÉTIER IMPORTANTE:
---------------------------

1. DEMANDES DE DISPONIBILITÉ:
   - Les locataires créent des demandes
   - Les propriétaires voient les demandes pour leurs annonces
   - Les propriétaires peuvent changer le statut (pending -> contacted -> closed)
   - Notifications envoyées si PropertyGroup.notifications_enabled = True

2. MESSAGES DE CONTACT:
   - Le premier message marque is_first_contact = True
   - Après le premier contact, les infos de contact du propriétaire sont révélées
   - Les messages marquent automatiquement is_read = True quand lus par le destinataire
   - Respect des préférences de notification par groupe

3. AVIS ET COMMENTAIRES:
   - Un utilisateur ne peut laisser qu'un seul avis par annonce
   - Les avis sont en attente de modération (status: pending)
   - Seuls les avis approuvés sont visibles publiquement
   - Les auteurs peuvent modifier/supprimer leurs avis avant approbation
   - Après approbation, l'admin doit modifier le statut pour permettre la modification

4. FAVORIS:
   - Un utilisateur ne peut ajouter qu'une fois la même annonce
   - La fonction toggle() permet d'ajouter/retirer facilement
   - La fonction check() permet de vérifier l'état favori d'une annonce

5. PERMISSIONS:
   - Public: Voir les avis approuvés
   - Locataires authentifiés: Créer demandes, messages, avis, gérer favoris
   - Propriétaires: Voir/gérer les demandes reçues, répondre aux messages
   - Admin: Modérer les avis, voir toutes les interactions
"""

"""