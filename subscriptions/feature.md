# Documentation API - Gestion des Abonnements LocHouse

## Table des matières
1. [Introduction](#introduction)
2. [Authentification](#authentification)
3. [Plans d'abonnement](#plans-dabonnement)
4. [Abonnements](#abonnements)
5. [Paiements](#paiements)
6. [Administration](#administration)
7. [Codes de statut](#codes-de-statut)

---

## Introduction

Cette API permet de gérer les plans d'abonnement, les souscriptions et les paiements via PayDunya pour la plateforme LocHouse.

**Base URL**: `/api/subscriptions/`

**Format de réponse**: JSON

---

## Authentification

La plupart des endpoints nécessitent une authentification via token JWT.

**Header requis**:
```
Authorization: Bearer <votre_token_jwt>
```

---

## Plans d'abonnement

### 1. Liste des plans d'abonnement

**Endpoint**: `GET /plans/`

**Permissions**: Public (tous les utilisateurs)

**Description**: Récupère la liste des plans d'abonnement actifs.

**Paramètres de requête**:
- `ordering`: Tri par `duration_months` ou `price` (ex: `-price`)

**Réponse** (200 OK):
```json
[
  {
    "id": 1,
    "name": "Plan Basic",
    "duration_months": 1,
    "price": "5000.00",
    "max_listings": 3,
    "is_premium": false,
    "has_priority_support": false,
    "has_featured_listings": false,
    "description": "Plan d'entrée pour démarrer",
    "is_active": true
  }
]
```

---

### 2. Détails d'un plan

**Endpoint**: `GET /plans/{id}/`

**Permissions**: Public

**Description**: Récupère les détails d'un plan spécifique.

**Réponse** (200 OK):
```json
{
  "id": 1,
  "name": "Plan Basic",
  "duration_months": 1,
  "price": "5000.00",
  "price_per_month": 5000.00,
  "max_listings": 3,
  "is_premium": false,
  "has_priority_support": false,
  "has_featured_listings": false,
  "description": "Plan d'entrée pour démarrer",
  "is_active": true,
  "features": [
    "Jusqu'à 3 annonces",
    "Durée: 1 mois"
  ]
}
```

---

### 3. Plans recommandés

**Endpoint**: `GET /plans/recommended/`

**Permissions**: Public

**Description**: Retourne les 3 plans les plus populaires.

**Réponse** (200 OK):
```json
[
  {
    "id": 2,
    "name": "Plan Premium",
    "duration_months": 6,
    "price": "25000.00",
    "max_listings": -1,
    "is_premium": true,
    "has_priority_support": true,
    "has_featured_listings": true,
    "description": "Le meilleur rapport qualité/prix",
    "is_active": true
  }
]
```

---

### 4. Créer un plan (Admin)

**Endpoint**: `POST /plans/`

**Permissions**: Admin uniquement

**Body**:
```json
{
  "name": "Plan Pro",
  "duration_months": 3,
  "price": "15000.00",
  "max_listings": 10,
  "is_premium": true,
  "has_priority_support": true,
  "has_featured_listings": false,
  "description": "Plan professionnel",
  "is_active": true
}
```

**Réponse** (201 Created):
```json
{
  "id": 3,
  "name": "Plan Pro",
  "duration_months": 3,
  "price": "15000.00",
  "max_listings": 10,
  "is_premium": true,
  "has_priority_support": true,
  "has_featured_listings": false,
  "description": "Plan professionnel",
  "is_active": true,
  "features": [...]
}
```

---

### 5. Modifier un plan (Admin)

**Endpoint**: `PUT /plans/{id}/` ou `PATCH /plans/{id}/`

**Permissions**: Admin uniquement

**Body**: Mêmes champs que la création (tous pour PUT, partiels pour PATCH)

---

### 6. Supprimer un plan (Admin)

**Endpoint**: `DELETE /plans/{id}/`

**Permissions**: Admin uniquement

**Réponse** (204 No Content)

---

## Abonnements

### 1. Liste des abonnements

**Endpoint**: `GET /subscriptions/`

**Permissions**: Authentifié

**Description**: Liste les abonnements de l'utilisateur (tous pour admin).

**Paramètres de requête**:
- `status`: Filtrer par statut (`trial`, `active`, `expired`, `cancelled`)
- `is_trial`: Filtrer par type (`true`, `false`)
- `plan`: Filtrer par plan (ID)
- `ordering`: Tri par date (`-created_at`, `start_date`, etc.)

**Réponse** (200 OK):
```json
[
  {
    "id": 1,
    "user": 5,
    "user_name": "John Doe",
    "plan": 2,
    "plan_name": "Plan Premium",
    "status": "active",
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-07-01T00:00:00Z",
    "is_trial": false,
    "auto_renew": true,
    "days_remaining": 157,
    "is_currently_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### 2. Détails d'un abonnement

**Endpoint**: `GET /subscriptions/{id}/`

**Permissions**: Propriétaire ou Admin

**Réponse** (200 OK):
```json
{
  "id": 1,
  "user": 5,
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "plan": 2,
  "plan_name": "Plan Premium",
  "plan_details": {
    "id": 2,
    "name": "Plan Premium",
    "duration_months": 6,
    "price": "25000.00",
    "max_listings": -1,
    "is_premium": true,
    "has_priority_support": true,
    "has_featured_listings": true,
    "description": "Le meilleur rapport qualité/prix",
    "is_active": true
  },
  "status": "active",
  "start_date": "2025-01-01T00:00:00Z",
  "end_date": "2025-07-01T00:00:00Z",
  "is_trial": false,
  "auto_renew": true,
  "days_remaining": 157,
  "is_currently_active": true,
  "total_paid": 25000.00,
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### 3. Créer un abonnement

**Endpoint**: `POST /subscriptions/`

**Permissions**: Authentifié

**Description**: Crée un nouvel abonnement. Le premier abonnement est un essai gratuit d'1 mois.

**Body**:
```json
{
  "plan": 2,
  "auto_renew": true
}
```

**Réponse** (201 Created):
```json
{
  "id": 2,
  "user": 5,
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "plan": 2,
  "plan_name": "Plan Premium",
  "plan_details": {...},
  "status": "trial",
  "start_date": "2025-11-05T10:00:00Z",
  "end_date": "2025-12-05T10:00:00Z",
  "is_trial": true,
  "auto_renew": true,
  "days_remaining": 30,
  "is_currently_active": true,
  "total_paid": 0.00,
  "created_at": "2025-11-05T10:00:00Z"
}
```

**Erreurs possibles**:
- 400: Plan inactif ou abonnement actif existant
- 401: Non authentifié

---

### 4. Abonnement actuel

**Endpoint**: `GET /subscriptions/current/`

**Permissions**: Authentifié

**Description**: Récupère l'abonnement actif de l'utilisateur connecté.

**Réponse** (200 OK):
```json
{
  "id": 1,
  "user": 5,
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "plan": 2,
  "plan_name": "Plan Premium",
  "plan_details": {...},
  "status": "active",
  "start_date": "2025-01-01T00:00:00Z",
  "end_date": "2025-07-01T00:00:00Z",
  "is_trial": false,
  "auto_renew": true,
  "days_remaining": 157,
  "is_currently_active": true,
  "total_paid": 25000.00,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Réponse si aucun abonnement** (200 OK):
```json
{
  "message": "Aucun abonnement actif",
  "has_subscription": false
}
```

---

### 5. Statut d'abonnement

**Endpoint**: `GET /subscriptions/status/`

**Permissions**: Authentifié

**Description**: Retourne le statut complet d'abonnement avec permissions de création d'annonces.

**Réponse** (200 OK):
```json
{
  "has_active_subscription": true,
  "current_subscription": {
    "id": 1,
    "user": 5,
    "plan": 2,
    "plan_name": "Plan Premium",
    "status": "active",
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-07-01T00:00:00Z",
    "is_trial": false,
    "auto_renew": true,
    "days_remaining": 157
  },
  "can_create_listings": true,
  "remaining_listings": -1,
  "days_remaining": 157
}
```

**Sans abonnement**:
```json
{
  "has_active_subscription": false,
  "current_subscription": null,
  "can_create_listings": false,
  "remaining_listings": 0,
  "days_remaining": 0
}
```

---

### 6. Historique des abonnements

**Endpoint**: `GET /subscriptions/history/`

**Permissions**: Authentifié

**Description**: Liste tous les abonnements passés et présents de l'utilisateur.

**Réponse** (200 OK): Liste d'abonnements

---

### 7. Annuler un abonnement

**Endpoint**: `POST /subscriptions/{id}/cancel/`

**Permissions**: Propriétaire ou Admin

**Description**: Annule un abonnement actif.

**Réponse** (200 OK):
```json
{
  "message": "Abonnement annulé avec succès",
  "data": {
    "id": 1,
    "status": "cancelled",
    "auto_renew": false,
    ...
  }
}
```

**Erreurs**:
- 400: Abonnement déjà terminé
- 403: Non autorisé

---

### 8. Renouveler un abonnement

**Endpoint**: `POST /subscriptions/{id}/renew/`

**Permissions**: Propriétaire ou Admin

**Description**: Crée un nouvel abonnement à partir d'un abonnement expiré.

**Réponse** (201 Created):
```json
{
  "message": "Nouvel abonnement créé. Veuillez procéder au paiement.",
  "data": {
    "id": 3,
    "status": "pending",
    "start_date": "2025-11-05T10:00:00Z",
    "end_date": "2026-05-05T10:00:00Z",
    ...
  }
}
```

**Erreurs**:
- 400: Abonnement actif existant
- 403: Non autorisé

---

### 9. Modifier un abonnement

**Endpoint**: `PATCH /subscriptions/{id}/`

**Permissions**: Propriétaire ou Admin

**Body**:
```json
{
  "auto_renew": false
}
```

**Ou** (Admin seulement):
```json
{
  "status": "active"
}
```

**Réponse** (200 OK): Abonnement mis à jour

---

## Paiements

### 1. Liste des paiements

**Endpoint**: `GET /payments/`

**Permissions**: Authentifié

**Description**: Liste les paiements de l'utilisateur (tous pour admin).

**Paramètres de requête**:
- `status`: Filtrer par statut (`pending`, `completed`, `failed`, `cancelled`)
- `payment_method`: Filtrer par méthode (`paydunya`)
- `subscription`: Filtrer par abonnement (ID)
- `ordering`: Tri (`-created_at`, `amount`, etc.)

**Réponse** (200 OK):
```json
[
  {
    "id": 1,
    "subscription": 1,
    "subscription_plan": "Plan Premium",
    "user_name": "John Doe",
    "amount": "25000.00",
    "payment_method": "paydunya",
    "status": "completed",
    "transaction_id": "PAY-ABC123DEF456",
    "paid_at": "2025-01-01T12:30:00Z",
    "created_at": "2025-01-01T12:00:00Z"
  }
]
```

---

### 2. Détails d'un paiement

**Endpoint**: `GET /payments/{id}/`

**Permissions**: Propriétaire ou Admin

**Réponse** (200 OK):
```json
{
  "id": 1,
  "subscription": 1,
  "subscription_plan": "Plan Premium",
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "amount": "25000.00",
  "payment_method": "paydunya",
  "status": "completed",
  "transaction_id": "PAY-ABC123DEF456",
  "payment_provider_response": {
    "token": "xyz789token",
    "response_code": "00",
    "status": "completed",
    "receipt_url": "https://app.paydunya.com/receipt/xyz789"
  },
  "paid_at": "2025-01-01T12:30:00Z",
  "created_at": "2025-01-01T12:00:00Z"
}
```

---

### 3. Initier un paiement

**Endpoint**: `POST /payments/initiate/`

**Permissions**: Authentifié

**Description**: Initie un paiement via PayDunya pour un abonnement.

**Body**:
```json
{
  "subscription": 1,
  "payment_method": "paydunya",
  "phone_number": "+22997123456"
}
```

**Réponse** (201 Created):
```json
{
  "message": "Paiement initié avec succès",
  "payment": {
    "id": 2,
    "subscription": 1,
    "amount": "25000.00",
    "payment_method": "paydunya",
    "status": "pending",
    "transaction_id": "PAY-XYZ987UVW654",
    "created_at": "2025-11-05T10:00:00Z"
  },
  "payment_url": "https://app.paydunya.com/sandbox-checkout/xyz789token",
  "token": "xyz789token"
}
```

**Instructions**:
1. Rediriger l'utilisateur vers `payment_url`
2. L'utilisateur effectue le paiement sur PayDunya
3. PayDunya appelle le webhook `/payments/callback/`
4. L'utilisateur est redirigé vers `return_url` (succès) ou `cancel_url` (annulation)

**Erreurs**:
- 400: Données invalides, essai gratuit, abonnement déjà actif
- 401: Non authentifié
- 403: Abonnement ne vous appartient pas

---

### 4. Callback PayDunya (Webhook)

**Endpoint**: `POST /payments/callback/` ou `GET /payments/callback/`

**Permissions**: Public (webhook PayDunya)

**Description**: Endpoint appelé automatiquement par PayDunya après paiement.

**Paramètres**:
- `token`: Token de la transaction PayDunya

**Réponse** (200 OK):
```json
{
  "message": "Paiement confirmé avec succès",
  "payment_id": 2
}
```

**Ou pour échec**:
```json
{
  "message": "Paiement annulé",
  "payment_id": 2
}
```

**Note**: Ce endpoint est appelé automatiquement par PayDunya. Ne pas l'appeler manuellement.

---

### 5. Vérifier un paiement

**Endpoint**: `GET /payments/{id}/verify/`

**Permissions**: Propriétaire ou Admin

**Description**: Vérifie manuellement le statut d'un paiement auprès de PayDunya.

**Réponse** (200 OK):
```json
{
  "payment_id": 2,
  "paydunya_status": "completed",
  "response": {
    "success": true,
    "status": "completed",
    "response_code": "00",
    "custom_data": {...},
    "receipt_url": "https://app.paydunya.com/receipt/xyz789"
  }
}
```

---

### 6. Mes paiements

**Endpoint**: `GET /payments/my_payments/`

**Permissions**: Authentifié

**Description**: Historique des paiements de l'utilisateur connecté.

**Réponse** (200 OK): Liste de paiements

---

### 7. Mettre à jour le statut (Admin)

**Endpoint**: `POST /payments/{id}/update_status/`

**Permissions**: Admin uniquement

**Description**: Met à jour manuellement le statut d'un paiement.

**Body**:
```json
{
  "status": "completed",
  "payment_provider_response": {...},
  "paid_at": "2025-11-05T10:30:00Z"
}
```

**Réponse** (200 OK):
```json
{
  "message": "Statut du paiement mis à jour",
  "data": {
    "id": 2,
    "status": "completed",
    ...
  }
}
```

**Note**: Si le statut passe à `completed`, l'abonnement associé est automatiquement activé.

---

### 8. Statistiques des paiements (Admin)

**Endpoint**: `GET /payments/statistics/`

**Permissions**: Admin uniquement

**Paramètres de requête**:
- `start_date`: Date de début (format: YYYY-MM-DD)
- `end_date`: Date de fin (format: YYYY-MM-DD)

**Réponse** (200 OK):
```json
{
  "total_payments": 150,
  "total_revenue": 3750000.00,
  "by_method": {
    "paydunya": {
      "count": 150,
      "revenue": 3750000.00
    }
  },
  "by_status": {
    "pending": 5,
    "completed": 140,
    "failed": 3,
    "cancelled": 2
  }
}
```

---

## Administration

### Dashboard administrateur

**Endpoint**: `GET /admin/dashboard/`

**Permissions**: Admin uniquement

**Description**: Statistiques globales du système d'abonnement.

**Réponse** (200 OK):
```json
{
  "total_subscriptions": 200,
  "active_subscriptions": 150,
  "trial_subscriptions": 30,
  "expired_subscriptions": 20,
  "total_revenue": 4500000.00,
  "revenue_this_month": 450000.00,
  "conversion_rate": 75.5
}
```

**Explication des champs**:
- `total_subscriptions`: Nombre total d'abonnements
- `active_subscriptions`: Abonnements actifs (trial + active)
- `trial_subscriptions`: Abonnements en période d'essai
- `expired_subscriptions`: Abonnements expirés
- `total_revenue`: Revenu total depuis le début
- `revenue_this_month`: Revenu du mois en cours
- `conversion_rate`: Taux de conversion essai → payant (%)

---

## Codes de statut

### Codes HTTP

- `200 OK`: Requête réussie
- `201 Created`: Ressource créée avec succès
- `204 No Content`: Suppression réussie
- `400 Bad Request`: Données invalides
- `401 Unauthorized`: Non authentifié
- `403 Forbidden`: Non autorisé
- `404 Not Found`: Ressource introuvable
- `500 Internal Server Error`: Erreur serveur

### Statuts d'abonnement

- `trial`: Période d'essai gratuite
- `active`: Abonnement actif et payé
- `expired`: Abonnement expiré
- `cancelled`: Abonnement annulé

### Statuts de paiement

- `pending`: En attente de confirmation
- `completed`: Paiement confirmé
- `failed`: Paiement échoué
- `cancelled`: Paiement annulé

---

## Flux de travail typique

### 1. Inscription et premier abonnement (essai gratuit)

```
1. GET /plans/ → Afficher les plans disponibles
2. POST /subscriptions/ → Créer abonnement (auto essai gratuit 1 mois)
3. GET /subscriptions/status/ → Vérifier le statut
```

### 2. Renouvellement après essai (paiement)

```
1. GET /subscriptions/current/ → Vérifier l'abonnement actuel
2. POST /subscriptions/ → Créer nouvel abonnement (status: pending)
3. POST /payments/initiate/ → Initier le paiement PayDunya
4. → Redirection vers PayDunya pour paiement
5. → PayDunya appelle /payments/callback/ (automatique)
6. GET /subscriptions/status/ → Vérifier activation
```

### 3. Vérification avant création d'annonce

```
1. GET /subscriptions/status/ → Vérifier permissions
2. Vérifier can_create_listings et remaining_listings
3. POST /listings/ → Créer l'annonce si autorisé
```

---

## Notes importantes

### PayDunya

- Mode test: Utiliser les numéros de test PayDunya
- Mode production: Configurer les vraies clés API dans settings.py
- Timeout des requêtes: 30 secondes
- Le callback est appelé automatiquement par PayDunya

### Sécurité

- Toujours vérifier les permissions avant modification
- Les tokens JWT expirent après 24h (configurable)
- Les webhooks PayDunya n'ont pas d'authentification (IP whitelisting recommandé)


## Support

Pour toute question ou problème, contactez ASSOUMA Z. Billa.