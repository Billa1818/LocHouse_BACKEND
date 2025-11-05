# Documentation API - App Core LocHouse

> **Version:** 1.0  
> **Date:** Novembre 2025  
> **Projet:** LocHouse - Plateforme de location immobilière

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Modèles de données](#modèles-de-données)
3. [API Endpoints](#api-endpoints)
4. [Tâches automatisées (Celery)](#tâches-automatisées-celery)
5. [Permissions et sécurité](#permissions-et-sécurité)
6. [Exemples d'utilisation](#exemples-dutilisation)
7. [Configuration](#configuration)

---

## Vue d'ensemble

L'application **Core** constitue le noyau fonctionnel de LocHouse. Elle gère :

- 📄 **Pages statiques** (CGU, FAQ, Politique de confidentialité)
- 🔔 **Notifications utilisateurs** (en temps réel et par email)
- 📊 **Analytiques et statistiques** (dashboard administrateur)
- ⚙️ **Tâches automatisées** (rappels, rapports, nettoyages)


## API Endpoints

### Pages statiques

#### **Liste des pages**

```http
GET /api/core/static-pages/
```

**Permissions:** Public (AllowAny)

**Réponse:**
```json
[
  {
    "id": 1,
    "slug": "terms-of-service",
    "title": "Conditions Générales d'Utilisation",
    "meta_description": "CGU de la plateforme LocHouse",
    "updated_at": "2025-11-05T10:30:00Z"
  }
]
```

---

#### **Détail d'une page**

```http
GET /api/core/static-pages/{slug}/
```

**Permissions:** Public (AllowAny)

**Exemple:**
```http
GET /api/core/static-pages/terms-of-service/
```

**Réponse:**
```json
{
  "id": 1,
  "slug": "terms-of-service",
  "title": "Conditions Générales d'Utilisation",
  "content": "# Article 1: Objet\n\nLes présentes CGU...",
  "meta_description": "CGU de la plateforme LocHouse",
  "is_published": true,
  "updated_at": "2025-11-05T10:30:00Z"
}
```

---

#### **Créer/Modifier/Supprimer une page**

```http
POST   /api/core/static-pages/
PUT    /api/core/static-pages/{slug}/
PATCH  /api/core/static-pages/{slug}/
DELETE /api/core/static-pages/{slug}/
```

**Permissions:** Admin uniquement (IsAdminUser)

**Body (POST/PUT):**
```json
{
  "slug": "faq",
  "title": "Questions Fréquentes",
  "content": "## Comment créer une annonce ?\n\n...",
  "meta_description": "FAQ de LocHouse",
  "is_published": true
}
```

---

### Notifications

#### **Liste des notifications utilisateur**

```http
GET /api/core/notifications/
```

**Permissions:** Authentifié (IsAuthenticated)

**Réponse:**
```json
[
  {
    "id": 42,
    "notification_type": "subscription_expiring",
    "notification_type_display": "Abonnement expire bientôt",
    "title": "Votre abonnement expire dans 7 jours",
    "message": "Votre abonnement Premium expire le 12/11/2025...",
    "link": "/dashboard/subscriptions/5/renew",
    "is_read": false,
    "created_at": "2025-11-05T08:00:00Z"
  }
]
```

---

#### **Nombre de notifications non lues**

```http
GET /api/core/notifications/unread_count/
```

**Permissions:** Authentifié

**Réponse:**
```json
{
  "unread_count": 5
}
```

---

#### **Marquer une notification comme lue**

```http
POST /api/core/notifications/{id}/mark_read/
```

**Permissions:** Authentifié (propriétaire uniquement)

**Réponse:**
```json
{
  "id": 42,
  "notification_type": "subscription_expiring",
  "is_read": true,
  "created_at": "2025-11-05T08:00:00Z"
}
```

---

#### **Marquer plusieurs notifications comme lues**

```http
POST /api/core/notifications/mark_multiple_read/
```

**Body (Option 1 - IDs spécifiques):**
```json
{
  "notification_ids": [42, 43, 44]
}
```

**Body (Option 2 - Tout marquer comme lu):**
```json
{
  "mark_all": true
}
```

**Réponse:**
```json
{
  "message": "3 notification(s) marquée(s) comme lue(s)",
  "updated_count": 3
}
```

---

#### **Supprimer toutes les notifications lues**

```http
DELETE /api/core/notifications/delete_all_read/
```

**Permissions:** Authentifié

**Réponse:**
```json
{
  "message": "8 notification(s) supprimée(s)",
  "deleted_count": 8
}
```

---

### Analytics (Admin uniquement)

#### **Liste des statistiques quotidiennes**

```http
GET /api/core/analytics/
```

**Permissions:** Admin (IsAdminUser)

**Réponse:**
```json
[
  {
    "id": 1,
    "date": "2025-11-04",
    "new_users": 12,
    "new_listings": 8,
    "active_subscriptions": 150,
    "revenue": "45000.00",
    "total_searches": 320,
    "total_contacts": 25
  }
]
```

---

#### **Résumé sur une période**

```http
GET /api/core/analytics/summary/?start_date=2025-10-01&end_date=2025-10-31
```

**Permissions:** Admin

**Query params:**
- `start_date` (optionnel) : Date de début (YYYY-MM-DD)
- `end_date` (optionnel) : Date de fin (YYYY-MM-DD)

**Par défaut:** 30 derniers jours

**Réponse:**
```json
{
  "total_users": 250,
  "total_listings": 180,
  "total_active_subscriptions": 150,
  "total_revenue": "1250000.00",
  "total_searches": 8500,
  "total_contacts": 420,
  "period_start": "2025-10-01",
  "period_end": "2025-10-31",
  "daily_breakdown": [
    {
      "id": 1,
      "date": "2025-10-01",
      "new_users": 8,
      "new_listings": 5,
      "active_subscriptions": 145,
      "revenue": "38000.00",
      "total_searches": 280,
      "total_contacts": 15
    }
  ]
}
```

---

#### **Dashboard administrateur complet**

```http
GET /api/core/analytics/dashboard/
```

**Permissions:** Admin

**Réponse complète:**
```json
{
  "total_users": 1250,
  "total_proprietaires": 450,
  "total_locataires": 800,
  "total_listings": 680,
  "published_listings": 620,
  "pending_listings": 35,
  "total_property_groups": 280,
  "active_subscriptions": 150,
  "expired_subscriptions": 45,
  "trial_subscriptions": 38,
  "total_revenue_today": "125000.00",
  "total_revenue_month": "3500000.00",
  "total_revenue_year": "42000000.00",
  "pending_identity_verifications": 12,
  "total_reviews": 340,
  "pending_reviews": 8,
  "total_availability_requests": 850,
  "pending_availability_requests": 22
}
```



## Codes d'erreur

| Code | Message | Description |
|------|---------|-------------|
| 200 | OK | Requête réussie |
| 201 | Created | Ressource créée |
| 400 | Bad Request | Données invalides |
| 401 | Unauthorized | Non authentifié |
| 403 | Forbidden | Pas les permissions |
| 404 | Not Found | Ressource introuvable |
| 500 | Internal Server Error | Erreur serveur |

---

## Support

Pour toute question ou problème, contactez ASSOUMA Z. Billa.