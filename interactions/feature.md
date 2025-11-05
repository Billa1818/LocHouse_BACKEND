# API Documentation - Interactions App

## Table des Matières
1. [Availability Requests](#availability-requests)
2. [Contact Messages](#contact-messages)
3. [Reviews](#reviews)
4. [Favorites](#favorites)

---

## 1. Availability Requests

### 1.1 Liste des demandes de disponibilité
```http
GET /api/interactions/availability-requests/
```

**Permissions:** Authentifié

**Filtres disponibles:**
- `status`: pending, contacted, closed
- `listing`: ID du listing

**Ordering:** `created_at`, `check_in_date`

**Search:** `message`, `listing__title`

**Réponse (200 OK):**
```json
{
  "count": 15,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "listing": 123,
      "listing_details": {
        "id": 123,
        "title": "Villa moderne",
        "property_name": "Résidence Les Palmiers",
        "category": "villa",
        "city": "Cotonou",
        "district": "Akpakpa",
        "daily_price": "25000.00",
        "monthly_price": "500000.00",
        "owner_name": "Jean Dupont",
        "cover_image": "https://..."
      },
      "requester": 456,
      "requester_details": {
        "id": 456,
        "full_name": "Marie Martin",
        "profile_name": "marie_m",
        "user_type": "locataire"
      },
      "requester_phone": "+22997123456",
      "message": "Je suis intéressé par cette propriété...",
      "check_in_date": "2025-12-01",
      "check_out_date": "2025-12-15",
      "guests_count": 4,
      "status": "pending",
      "owner_notified": true,
      "created_at": "2025-11-05T10:30:00Z"
    }
  ]
}
```

---

### 1.2 Créer une demande de disponibilité
```http
POST /api/interactions/availability-requests/
```

**Permissions:** Authentifié

**Body:**
```json
{
  "listing": 123,
  "requester_phone": "+22997123456",
  "message": "Je souhaite louer cette propriété...",
  "check_in_date": "2025-12-01",
  "check_out_date": "2025-12-15",
  "guests_count": 4
}
```

**Validations:**
- `check_out_date` doit être après `check_in_date`
- `check_in_date` ne peut pas être dans le passé
- Le listing doit être publié

**Réponse (201 Created):**
```json
{
  "id": 1,
  "listing": 123,
  "listing_details": {...},
  "requester": 456,
  "requester_details": {...},
  "requester_phone": "+22997123456",
  "message": "Je souhaite louer cette propriété...",
  "check_in_date": "2025-12-01",
  "check_out_date": "2025-12-15",
  "guests_count": 4,
  "status": "pending",
  "owner_notified": true,
  "created_at": "2025-11-05T10:30:00Z"
}
```

**Note:** Une notification est automatiquement créée pour le propriétaire si les notifications sont activées pour le groupe.

---

### 1.3 Détail d'une demande
```http
GET /api/interactions/availability-requests/{id}/
```

**Permissions:** Authentifié (requester ou propriétaire du listing)

**Réponse (200 OK):** Même structure que la création

---

### 1.4 Mettre à jour le statut (propriétaire)
```http
PATCH /api/interactions/availability-requests/{id}/update_status/
```

**Permissions:** Authentifié + Propriétaire du listing

**Body:**
```json
{
  "status": "contacted"
}
```

**Valeurs possibles:** `pending`, `contacted`, `closed`

**Réponse (200 OK):**
```json
{
  "message": "Statut mis à jour avec succès",
  "data": {
    "id": 1,
    "status": "contacted",
    ...
  }
}
```

---

### 1.5 Mes demandes (locataire)
```http
GET /api/interactions/availability-requests/my_requests/
```

**Permissions:** Authentifié

**Description:** Liste toutes les demandes créées par l'utilisateur connecté

**Réponse (200 OK):** Liste paginée des demandes

---

### 1.6 Demandes reçues (propriétaire)
```http
GET /api/interactions/availability-requests/received_requests/
```

**Permissions:** Authentifié + Type propriétaire

**Paramètres query:**
- `status`: Filtrer par statut
- `listing_id`: Filtrer par listing

**Réponse (200 OK):** Liste paginée des demandes reçues

---

## 2. Contact Messages

### 2.1 Liste des messages
```http
GET /api/interactions/messages/
```

**Permissions:** Authentifié

**Filtres disponibles:**
- `listing`: ID du listing
- `is_read`: true/false

**Ordering:** `created_at`

**Réponse (200 OK):**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "listing": 123,
      "listing_title": "Villa moderne",
      "sender": 456,
      "sender_name": "Marie Martin",
      "receiver": 789,
      "receiver_name": "Jean Dupont",
      "message_preview": "Bonjour, je suis intéressé par...",
      "is_read": false,
      "created_at": "2025-11-05T10:30:00Z"
    }
  ]
}
```

---

### 2.2 Envoyer un message
```http
POST /api/interactions/messages/
```

**Permissions:** Authentifié

**Body:**
```json
{
  "listing": 123,
  "message": "Bonjour, je suis intéressé par cette propriété..."
}
```

**Validations:**
- Le listing doit être publié
- On ne peut pas contacter sa propre annonce

**Réponse (201 Created):**
```json
{
  "id": 1,
  "listing": 123,
  "listing_details": {...},
  "sender": 456,
  "sender_details": {...},
  "receiver": 789,
  "receiver_details": {...},
  "message": "Bonjour, je suis intéressé...",
  "is_first_contact": true,
  "is_read": false,
  "owner_contact": {
    "id": 789,
    "full_name": "Jean Dupont",
    "email": "jean@example.com",
    "phone_number": "+22997654321",
    "profile_name": "jean_dupont"
  },
  "created_at": "2025-11-05T10:30:00Z"
}
```

**Note:** Le champ `owner_contact` est révélé uniquement après le premier message envoyé.

---

### 2.3 Conversations groupées
```http
GET /api/interactions/messages/conversations/
```

**Permissions:** Authentifié

**Description:** Liste les conversations groupées par listing (dernier message de chaque conversation)

**Réponse (200 OK):**
```json
[
  {
    "id": 5,
    "listing": 123,
    "listing_title": "Villa moderne",
    "sender": 456,
    "sender_name": "Marie Martin",
    "receiver": 789,
    "receiver_name": "Jean Dupont",
    "message_preview": "D'accord, je vous recontacte...",
    "is_read": true,
    "created_at": "2025-11-05T14:30:00Z"
  }
]
```

---

### 2.4 Détail d'une conversation
```http
GET /api/interactions/messages/conversation_detail/?listing_id=123
```

**Permissions:** Authentifié

**Paramètre requis:** `listing_id`

**Description:** Tous les messages d'une conversation spécifique, ordonnés par date

**Effet secondaire:** Marque automatiquement comme lus les messages reçus

**Réponse (200 OK):**
```json
[
  {
    "id": 1,
    "listing": 123,
    "listing_details": {...},
    "sender": 456,
    "sender_details": {...},
    "receiver": 789,
    "receiver_details": {...},
    "message": "Bonjour, je suis intéressé...",
    "is_first_contact": true,
    "is_read": true,
    "owner_contact": {...},
    "created_at": "2025-11-05T10:30:00Z"
  },
  {
    "id": 2,
    "message": "Bonjour, merci pour votre intérêt...",
    "is_first_contact": false,
    ...
  }
]
```

---

### 2.5 Marquer comme lu
```http
PATCH /api/interactions/messages/{id}/mark_as_read/
```

**Permissions:** Authentifié (receiver uniquement)

**Réponse (200 OK):**
```json
{
  "message": "Message marqué comme lu"
}
```

---

### 2.6 Nombre de messages non lus
```http
GET /api/interactions/messages/unread_count/
```

**Permissions:** Authentifié

**Réponse (200 OK):**
```json
{
  "unread_count": 5
}
```

---

## 3. Reviews

### 3.1 Liste des avis
```http
GET /api/interactions/reviews/
```

**Permissions:** Public (voit uniquement les avis approuvés)

**Filtres disponibles:**
- `listing`: ID du listing
- `status`: pending, approved, rejected (admin uniquement)
- `rating`: 1-5

**Ordering:** `created_at`, `rating`

**Réponse (200 OK):**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "listing": 123,
      "listing_details": {...},
      "author": 456,
      "author_details": {
        "id": 456,
        "full_name": "Marie Martin",
        "profile_name": "marie_m",
        "user_type": "locataire"
      },
      "rating": 5,
      "comment": "Excellent logement, très propre...",
      "status": "approved",
      "rejection_reason": null,
      "created_at": "2025-11-01T10:00:00Z",
      "approved_at": "2025-11-02T09:00:00Z"
    }
  ]
}
```

---

### 3.2 Créer un avis
```http
POST /api/interactions/reviews/
```

**Permissions:** Authentifié

**Body:**
```json
{
  "listing": 123,
  "rating": 5,
  "comment": "Excellent logement, très propre et bien situé..."
}
```

**Validations:**
- Note entre 1 et 5
- Le listing doit être publié
- On ne peut pas laisser d'avis sur sa propre annonce
- Un seul avis par utilisateur et par annonce

**Réponse (201 Created):**
```json
{
  "id": 1,
  "listing": 123,
  "listing_details": {...},
  "author": 456,
  "author_details": {...},
  "rating": 5,
  "comment": "Excellent logement...",
  "status": "pending",
  "rejection_reason": null,
  "created_at": "2025-11-05T10:30:00Z",
  "approved_at": null
}
```

**Note:** L'avis est créé avec le statut `pending` et nécessite une modération admin.

---

### 3.3 Modifier un avis
```http
PUT/PATCH /api/interactions/reviews/{id}/
```

**Permissions:** Authentifié (auteur uniquement)

**Body:** Même structure que la création

---

### 3.4 Supprimer un avis
```http
DELETE /api/interactions/reviews/{id}/
```

**Permissions:** Authentifié (auteur uniquement)

**Réponse (204 No Content)**

---

### 3.5 Modérer un avis (admin)
```http
PATCH /api/interactions/reviews/{id}/moderate/
```

**Permissions:** Admin uniquement

**Body (Approbation):**
```json
{
  "status": "approved"
}
```

**Body (Rejet):**
```json
{
  "status": "rejected",
  "rejection_reason": "Contenu inapproprié"
}
```

**Réponse (200 OK):**
```json
{
  "message": "Avis modéré avec succès",
  "data": {
    "id": 1,
    "status": "approved",
    "approved_at": "2025-11-05T10:30:00Z",
    ...
  }
}
```

**Note:** L'auteur reçoit automatiquement une notification.

---

### 3.6 Avis en attente (admin)
```http
GET /api/interactions/reviews/pending_reviews/
```

**Permissions:** Admin uniquement

**Description:** Liste tous les avis en attente de modération

**Réponse (200 OK):** Liste paginée des avis pending

---

### 3.7 Mes avis
```http
GET /api/interactions/reviews/my_reviews/
```

**Permissions:** Authentifié

**Description:** Liste tous les avis créés par l'utilisateur

**Réponse (200 OK):**
```json
[
  {
    "id": 1,
    "listing": 123,
    "listing_details": {...},
    "rating": 5,
    "comment": "...",
    "status": "approved",
    ...
  }
]
```

---

### 3.8 Statistiques d'un listing
```http
GET /api/interactions/reviews/listing_stats/?listing_id=123
```

**Permissions:** Public

**Paramètre requis:** `listing_id`

**Réponse (200 OK):**
```json
{
  "average_rating": 4.5,
  "total_reviews": 12,
  "rating_distribution": {
    "rating_1": 0,
    "rating_2": 1,
    "rating_3": 2,
    "rating_4": 3,
    "rating_5": 6
  }
}
```

---

## 4. Favorites

### 4.1 Liste des favoris
```http
GET /api/interactions/favorites/
```

**Permissions:** Authentifié

**Description:** Liste tous les favoris de l'utilisateur

**Réponse (200 OK):**
```json
[
  {
    "id": 1,
    "listing": 123,
    "listing_details": {
      "id": 123,
      "title": "Villa moderne",
      "property_name": "Résidence Les Palmiers",
      "category": "villa",
      "city": "Cotonou",
      "district": "Akpakpa",
      "daily_price": "25000.00",
      "monthly_price": "500000.00",
      "owner_name": "Jean Dupont",
      "cover_image": "https://..."
    },
    "created_at": "2025-11-01T10:00:00Z"
  }
]
```

---

### 4.2 Ajouter aux favoris
```http
POST /api/interactions/favorites/
```

**Permissions:** Authentifié

**Body:**
```json
{
  "listing": 123
}
```

**Validation:** Le listing doit être publié

**Réponse (201 Created):**
```json
{
  "id": 1,
  "listing": 123,
  "listing_details": {...},
  "created_at": "2025-11-05T10:30:00Z"
}
```

**Note:** Si déjà en favoris, retourne le favori existant.

---

### 4.3 Retirer des favoris
```http
DELETE /api/interactions/favorites/{id}/
```

**Permissions:** Authentifié (propriétaire du favori)

**Réponse (204 No Content)**

---

### 4.4 Toggle favori
```http
POST /api/interactions/favorites/toggle/
```

**Permissions:** Authentifié

**Body:**
```json
{
  "listing": 123
}
```

**Réponse (200 OK - Ajouté):**
```json
{
  "message": "Ajouté aux favoris",
  "is_favorite": true,
  "data": {
    "id": 1,
    "listing": 123,
    "listing_details": {...},
    "created_at": "2025-11-05T10:30:00Z"
  }
}
```

**Réponse (200 OK - Retiré):**
```json
{
  "message": "Retiré des favoris",
  "is_favorite": false
}
```

---

### 4.5 Vérifier si en favoris
```http
GET /api/interactions/favorites/check/?listing_id=123
```

**Permissions:** Authentifié

**Paramètre requis:** `listing_id`

**Réponse (200 OK):**
```json
{
  "is_favorite": true
}
```

---

## Codes d'Erreur Communs

### 400 Bad Request
```json
{
  "field_name": ["Message d'erreur de validation"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Les informations d'authentification n'ont pas été fournies."
}
```

### 403 Forbidden
```json
{
  "error": "Vous n'avez pas la permission d'effectuer cette action"
}
```

### 404 Not Found
```json
{
  "detail": "Introuvable."
}
```

---

## Notes Importantes

### Permissions
- **Public:** Lecture seule des avis approuvés
- **Locataire:** Création de demandes, messages, avis, favoris
- **Propriétaire:** Gestion des demandes reçues, réponse aux messages
- **Admin:** Accès complet + modération des avis

### Notifications
- Créées automatiquement si activées au niveau du groupe de propriétés
- Types: `new_availability_request`, `new_message`, `new_review`

### Révélation Contact
Le contact du propriétaire (email, téléphone) n'est révélé qu'après le premier message envoyé par le locataire.

### Pagination
Toutes les listes sont paginées par défaut (10 items par page)