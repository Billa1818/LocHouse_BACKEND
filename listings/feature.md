# Documentation API - Module Listings

## Table des matières
1. [PropertyGroup Endpoints](#propertygroup-endpoints)
2. [Listing Endpoints](#listing-endpoints)
3. [Amenity Endpoints](#amenity-endpoints)
4. [Modèles de données](#modèles-de-données)

---

## PropertyGroup Endpoints

### 1. Lister tous les groupes de propriétés
**GET** `/api/listings/property-groups/`

**Permissions:** Authentification requise (propriétaire)

**Description:** Liste tous les groupes de propriétés de l'utilisateur connecté. Les admins voient tous les groupes.

**Query Parameters:**
- `search` (string, optionnel) : Recherche dans nom et description
- `ordering` (string, optionnel) : Tri (`name`, `created_at`, `updated_at`, `-created_at`, etc.)

**Response 200:**
```json
[
  {
    "id": 1,
    "name": "Hôtel Dallas",
    "description": "Ensemble de chambres d'hôtel",
    "notifications_enabled": true,
    "owner_name": "Jean Dupont",
    "listings_count": 5,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:45:00Z"
  }
]
```

---

### 2. Créer un groupe de propriétés
**POST** `/api/listings/property-groups/`

**Permissions:** Authentification requise (propriétaire)

**Limitations:**
- **Sans abonnement:** Maximum 5 groupes pendant 30 jours d'essai gratuit
- **Après 30 jours sans abonnement:** Tous les groupes sont supprimés
- **Avec abonnement actif:** Création illimitée

**Request Body:**
```json
{
  "name": "Résidence Le Palmier",
  "description": "Appartements modernes au centre-ville",
  "notifications_enabled": true
}
```

**Response 201:**
```json
{
  "id": 2,
  "name": "Résidence Le Palmier",
  "description": "Appartements modernes au centre-ville",
  "notifications_enabled": true
}
```

**Response 403 (Limite atteinte):**
```json
{
  "error": "Limite atteinte : 5 groupes maximum pendant l'essai gratuit",
  "detail": {
    "current_count": 5,
    "max_allowed": 5,
    "trial_days_remaining": 15,
    "trial_end_date": "2025-02-14T00:00:00Z"
  },
  "upgrade_required": true
}
```

**Response 403 (Essai expiré):**
```json
{
  "error": "Votre période d'essai gratuit de 30 jours est expirée",
  "detail": {
    "trial_started": "2024-12-15T00:00:00Z",
    "trial_ended": "2025-01-14T00:00:00Z",
    "days_since_expiry": 5
  },
  "upgrade_required": true
}
```

---

### 3. Détails d'un groupe
**GET** `/api/listings/property-groups/{id}/`

**Permissions:** Authentification requise (propriétaire du groupe)

**Response 200:**
```json
{
  "id": 1,
  "owner": 12,
  "name": "Hôtel Dallas",
  "description": "Ensemble de chambres d'hôtel",
  "notifications_enabled": true,
  "owner_name": "Jean Dupont",
  "listings_count": 5,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-20T14:45:00Z"
}
```

---

### 4. Mettre à jour un groupe
**PUT/PATCH** `/api/listings/property-groups/{id}/`

**Permissions:** Authentification requise (propriétaire du groupe)

**Request Body (PATCH):**
```json
{
  "name": "Hôtel Dallas Premium",
  "notifications_enabled": false
}
```

**Response 200:**
```json
{
  "id": 1,
  "name": "Hôtel Dallas Premium",
  "description": "Ensemble de chambres d'hôtel",
  "notifications_enabled": false
}
```

---

### 5. Supprimer un groupe
**DELETE** `/api/listings/property-groups/{id}/`

**Permissions:** Authentification requise (propriétaire du groupe)

**Response 204:** No Content

---

### 6. Activer/désactiver les notifications
**POST** `/api/listings/property-groups/{id}/toggle_notifications/`

**Permissions:** Authentification requise (propriétaire du groupe)

**Description:** Bascule l'état des notifications pour le groupe.

**Response 200:**
```json
{
  "message": "Notifications activées",
  "data": {
    "id": 1,
    "owner": 12,
    "name": "Hôtel Dallas",
    "notifications_enabled": true,
    "owner_name": "Jean Dupont",
    "listings_count": 5,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:45:00Z"
  }
}
```

---

### 7. Lister les annonces d'un groupe
**GET** `/api/listings/property-groups/{id}/listings/`

**Permissions:** Authentification requise (propriétaire du groupe)

**Response 200:**
```json
[
  {
    "id": 101,
    "title": "Chambre double vue mer",
    "property_name": "Chambre 204",
    "category": "touristique",
    "status": "published",
    "daily_price": "25000.00",
    "monthly_price": null,
    "city": "Cotonou",
    "district": "Cadjehoun",
    "bedrooms": 1,
    "bathrooms": 1,
    "area": "20.00",
    "views_count": 45,
    "owner_name": "Jean Dupont",
    "property_group_name": "Hôtel Dallas",
    "cover_image": "https://example.com/media/listings/image1.jpg",
    "amenities": [...],
    "created_at": "2025-01-10T08:00:00Z",
    "published_at": "2025-01-11T10:00:00Z"
  }
]
```

---

### 8. Statistiques d'un groupe
**GET** `/api/listings/property-groups/{id}/statistics/`

**Permissions:** Authentification requise (propriétaire du groupe)

**Response 200:**
```json
{
  "total_listings": 5,
  "published_listings": 4,
  "pending_listings": 1,
  "total_views": 230,
  "notifications_enabled": true
}
```

---

## Listing Endpoints

### 1. Lister toutes les annonces
**GET** `/api/listings/listings/`

**Permissions:** Lecture publique (les non-authentifiés voient seulement les annonces publiées)

**Description:** 
- **Non authentifié:** Annonces publiées uniquement
- **Propriétaire authentifié:** Annonces publiées + ses propres annonces (tous statuts)
- **Admin:** Toutes les annonces

**Query Parameters:**
- `search` (string) : Recherche dans titre, description, ville, quartier, nom de propriété
- `category` (string) : `residentiel` ou `touristique`
- `status` (string) : `draft`, `pending`, `published`, `rejected`, `archived`
- `city` (string) : Filtrer par ville
- `district` (string) : Filtrer par quartier
- `min_price` (decimal) : Prix minimum
- `max_price` (decimal) : Prix maximum
- `bedrooms` (integer) : Nombre de chambres
- `bathrooms` (integer) : Nombre de salles de bain
- `ordering` (string) : Tri (`created_at`, `published_at`, `daily_price`, `-views_count`, etc.)

**Response 200:**
```json
[
  {
    "id": 101,
    "title": "Appartement 2 chambres meublé",
    "property_name": "Appart A12",
    "category": "residentiel",
    "status": "published",
    "daily_price": null,
    "monthly_price": "150000.00",
    "city": "Cotonou",
    "district": "Akpakpa",
    "bedrooms": 2,
    "bathrooms": 1,
    "area": "65.00",
    "views_count": 45,
    "owner_name": "Jean Dupont",
    "property_group_name": "Résidence Le Palmier",
    "cover_image": "https://example.com/media/listings/cover1.jpg",
    "amenities": [
      {
        "id": 1,
        "name": "WiFi",
        "icon": "wifi"
      },
      {
        "id": 2,
        "name": "Climatisation",
        "icon": "ac"
      }
    ],
    "created_at": "2025-01-10T08:00:00Z",
    "published_at": "2025-01-11T10:00:00Z"
  }
]
```

---

### 2. Créer une annonce
**POST** `/api/listings/listings/`

**Permissions:** Authentification requise (propriétaire)

**Description:** Crée une annonce avec statut `pending` (en attente de validation admin).

**Request Body (multipart/form-data):**
```json
{
  "property_group": 1,
  "title": "Studio moderne centre-ville",
  "description": "Magnifique studio de 30m² entièrement meublé avec cuisine équipée, salle de bain moderne. Idéal pour célibataire ou couple. Proche commerces et transports.",
  "property_name": "Studio B5",
  "category": "residentiel",
  "daily_price": null,
  "monthly_price": "120000.00",
  "city": "Cotonou",
  "district": "Haie Vive",
  "address": "Rue 123, Immeuble Le Phénix",
  "latitude": "6.3654",
  "longitude": "2.4183",
  "bedrooms": 1,
  "bathrooms": 1,
  "area": "30.00",
  "amenity_ids": [1, 2, 5, 8],
  "media_files": ["file1.jpg", "file2.jpg", "file3.jpg"]
}
```

**Validations:**
- Titre minimum 10 caractères
- Description minimum 50 caractères
- Au moins un prix (journalier ou mensuel)
- Si `property_group` fourni, doit appartenir au propriétaire

**Response 201:**
```json
{
  "id": 105,
  "property_group": 1,
  "title": "Studio moderne centre-ville",
  "description": "Magnifique studio de 30m²...",
  "property_name": "Studio B5",
  "category": "residentiel",
  "daily_price": null,
  "monthly_price": "120000.00",
  "city": "Cotonou",
  "district": "Haie Vive",
  "address": "Rue 123, Immeuble Le Phénix",
  "latitude": "6.3654",
  "longitude": "2.4183",
  "bedrooms": 1,
  "bathrooms": 1,
  "area": "30.00"
}
```

**Response 400 (Validation):**
```json
{
  "title": ["Le titre doit contenir au moins 10 caractères."],
  "description": ["La description doit contenir au moins 50 caractères."]
}
```

---

### 3. Détails d'une annonce
**GET** `/api/listings/listings/{id}/`

**Permissions:** Lecture publique pour annonces publiées, authentification requise pour autres statuts

**Description:** Incrémente automatiquement `views_count` (sauf pour le propriétaire).

**Response 200:**
```json
{
  "id": 101,
  "owner": 12,
  "owner_name": "Jean Dupont",
  "owner_profile_name": "Jean D.",
  "owner_email": null,
  "owner_phone": null,
  "property_group": 1,
  "property_group_name": "Résidence Le Palmier",
  "property_group_id": 1,
  "title": "Appartement 2 chambres meublé",
  "description": "Bel appartement de 65m² situé dans une résidence calme...",
  "property_name": "Appart A12",
  "category": "residentiel",
  "daily_price": null,
  "monthly_price": "150000.00",
  "city": "Cotonou",
  "district": "Akpakpa",
  "address": "Rue de la Paix, Résidence Le Palmier",
  "latitude": "6.3700",
  "longitude": "2.4200",
  "bedrooms": 2,
  "bathrooms": 1,
  "area": "65.00",
  "status": "published",
  "rejection_reason": null,
  "views_count": 46,
  "media": [
    {
      "id": 1,
      "media_type": "image",
      "file": "https://example.com/media/listings/img1.jpg",
      "video_url": null,
      "order": 0,
      "is_cover": true,
      "uploaded_at": "2025-01-10T08:30:00Z"
    }
  ],
  "amenities": [
    {
      "id": 1,
      "name": "WiFi",
      "icon": "wifi"
    }
  ],
  "notifications_enabled": true,
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-20T10:00:00Z",
  "published_at": "2025-01-11T10:00:00Z"
}
```

**Note:** `owner_email` et `owner_phone` sont `null` par défaut. Ils seront visibles après premier contact (fonctionnalité à implémenter avec le module de messagerie).

---

### 4. Mettre à jour une annonce
**PUT/PATCH** `/api/listings/listings/{id}/`

**Permissions:** Authentification requise (propriétaire de l'annonce)

**Description:** 
- Modification de champs majeurs (titre, description, prix, adresse) remet le statut en `pending`
- Peut ajouter de nouveaux médias sans supprimer les existants
- Peut mettre à jour les équipements

**Request Body (PATCH):**
```json
{
  "title": "Appartement 2 chambres meublé - Disponible immédiatement",
  "monthly_price": "140000.00",
  "amenity_ids": [1, 2, 3, 5],
  "media_files": ["new_photo.jpg"]
}
```

**Response 200:**
```json
{
  "id": 101,
  "property_group": 1,
  "title": "Appartement 2 chambres meublé - Disponible immédiatement",
  "description": "Bel appartement de 65m²...",
  "property_name": "Appart A12",
  "category": "residentiel",
  "daily_price": null,
  "monthly_price": "140000.00",
  "city": "Cotonou",
  "district": "Akpakpa",
  "address": "Rue de la Paix, Résidence Le Palmier",
  "latitude": "6.3700",
  "longitude": "2.4200",
  "bedrooms": 2,
  "bathrooms": 1,
  "area": "65.00"
}
```

---

### 5. Supprimer une annonce
**DELETE** `/api/listings/listings/{id}/`

**Permissions:** Authentification requise (propriétaire de l'annonce)

**Response 204:** No Content

---

### 6. Mes annonces
**GET** `/api/listings/listings/my_listings/`

**Permissions:** Authentification requise

**Description:** Liste toutes les annonces du propriétaire connecté (tous statuts).

**Response 200:**
```json
[
  {
    "id": 101,
    "title": "Appartement 2 chambres meublé",
    "status": "published",
    ...
  },
  {
    "id": 102,
    "title": "Studio économique",
    "status": "pending",
    ...
  }
]
```

---

### 7. Dashboard propriétaire
**GET** `/api/listings/listings/my_dashboard/`

**Permissions:** Authentification requise (propriétaire)

**Description:** Statistiques globales du propriétaire.

**Response 200:**
```json
{
  "total_listings": 8,
  "published": 5,
  "pending": 2,
  "draft": 1,
  "rejected": 0,
  "total_views": 456,
  "groups": [
    {
      "id": 1,
      "name": "Hôtel Dallas",
      "description": "Ensemble de chambres d'hôtel",
      "notifications_enabled": true,
      "owner_name": "Jean Dupont",
      "listings_count": 5,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-20T14:45:00Z"
    }
  ]
}
```

---

### 8. Mettre à jour le statut (Admin)
**POST** `/api/listings/listings/{id}/update_status/`

**Permissions:** Authentification requise (Admin uniquement)

**Description:** Valider, rejeter ou archiver une annonce.

**Request Body:**
```json
{
  "status": "published"
}
```

**Ou pour rejet:**
```json
{
  "status": "rejected",
  "rejection_reason": "Photos de mauvaise qualité. Veuillez soumettre des photos plus claires."
}
```

**Validations:**
- Si `status` = `rejected`, `rejection_reason` est obligatoire

**Response 200:**
```json
{
  "message": "Statut mis à jour avec succès",
  "data": {
    "id": 101,
    "status": "published",
    "published_at": "2025-01-22T15:30:00Z",
    ...
  }
}
```

**Response 400:**
```json
{
  "rejection_reason": ["Une raison de rejet est obligatoire."]
}
```

---

### 9. Annonces en attente (Admin)
**GET** `/api/listings/listings/pending_listings/`

**Permissions:** Authentification requise (Admin uniquement)

**Description:** Liste toutes les annonces avec statut `pending`.

**Response 200:**
```json
[
  {
    "id": 103,
    "title": "Villa 4 chambres avec piscine",
    "status": "pending",
    "created_at": "2025-01-21T10:00:00Z",
    ...
  }
]
```

---

### 10. Ajouter aux favoris
**POST** `/api/listings/listings/{id}/add_to_favorites/`

**Permissions:** Authentification requise

**Description:** Ajoute l'annonce aux favoris de l'utilisateur (locataire).

**Response 200:**
```json
{
  "message": "Ajouté aux favoris avec succès",
  "listing_id": "101"
}
```

---

### 11. Supprimer un média
**DELETE** `/api/listings/listings/{id}/delete_media/`

**Permissions:** Authentification requise (propriétaire de l'annonce)

**Request Body:**
```json
{
  "media_id": 5
}
```

**Response 200:**
```json
{
  "message": "Média supprimé avec succès"
}
```

**Response 400:**
```json
{
  "error": "media_id requis"
}
```

**Response 404:**
```json
{
  "error": "Média introuvable"
}
```

---

## Amenity Endpoints

### 1. Lister tous les équipements
**GET** `/api/listings/amenities/`

**Permissions:** Aucune (lecture publique)

**Query Parameters:**
- `search` (string) : Recherche par nom

**Response 200:**
```json
[
  {
    "id": 1,
    "name": "WiFi",
    "icon": "wifi"
  },
  {
    "id": 2,
    "name": "Climatisation",
    "icon": "ac"
  },
  {
    "id": 3,
    "name": "Parking",
    "icon": "parking"
  }
]
```

---

### 2. Détails d'un équipement
**GET** `/api/listings/amenities/{id}/`

**Permissions:** Aucune (lecture publique)

**Response 200:**
```json
{
  "id": 1,
  "name": "WiFi",
  "icon": "wifi"
}
```

---

## Modèles de données

### PropertyGroup
```json
{
  "id": integer,
  "owner": integer (User ID),
  "name": string (max 200 chars),
  "description": string (nullable),
  "notifications_enabled": boolean,
  "created_at": datetime,
  "updated_at": datetime
}
```

### Listing
```json
{
  "id": integer,
  "owner": integer (User ID),
  "property_group": integer (PropertyGroup ID, nullable),
  "title": string (max 200 chars),
  "description": text,
  "property_name": string (max 200 chars, nullable),
  "category": "residentiel" | "touristique",
  "daily_price": decimal (nullable),
  "monthly_price": decimal (nullable),
  "city": string (max 100 chars),
  "district": string (max 100 chars),
  "address": text,
  "latitude": decimal (nullable),
  "longitude": decimal (nullable),
  "bedrooms": integer,
  "bathrooms": integer,
  "area": decimal (m², nullable),
  "status": "draft" | "pending" | "published" | "rejected" | "archived",
  "rejection_reason": text (nullable),
  "views_count": integer,
  "created_at": datetime,
  "updated_at": datetime,
  "published_at": datetime (nullable)
}
```

### ListingMedia
```json
{
  "id": integer,
  "listing": integer (Listing ID),
  "media_type": "image" | "video",
  "file": file,
  "video_url": url (nullable),
  "order": integer,
  "is_cover": boolean,
  "uploaded_at": datetime
}
```

### ListingAmenity
```json
{
  "id": integer,
  "name": string (max 100 chars),
  "icon": string (max 50 chars, nullable)
}
```

---

## Codes d'erreur courants

- **400 Bad Request:** Données invalides
- **401 Unauthorized:** Authentification requise
- **403 Forbidden:** Permissions insuffisantes ou limite atteinte
- **404 Not Found:** Ressource introuvable
- **201 Created:** Ressource créée avec succès
- **204 No Content:** Suppression réussie

---

## Notes importantes

1. **Limitation PropertyGroup:** Sans abonnement, maximum 5 groupes pendant 30 jours d'essai. Après expiration, tous les groupes sont supprimés automatiquement.

2. **Validation des annonces:** Toutes les annonces créées ou modifiées (champs majeurs) passent en statut `pending` et nécessitent validation admin.

3. **Compteur de vues:** S'incrémente automatiquement à chaque consultation, sauf pour le propriétaire.

4. **Notifications:** Gérées au niveau du `PropertyGroup`. Si une annonce appartient à un groupe, elle hérite de ses paramètres de notification.

5. **Contact propriétaire:** L'email et le téléphone du propriétaire ne sont visibles qu'après premier contact (fonctionnalité à implémenter avec le module de messagerie).


## Support

Pour toute question ou problème, contactez ASSOUMA Z. Billa.