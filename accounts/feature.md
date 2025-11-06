# Documentation API - Application accounts

## Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Authentification](#authentification)
3. [Endpoints Publics](#endpoints-publics)
4. [Endpoints Utilisateur](#endpoints-utilisateur)
5. [Endpoints Admin](#endpoints-admin)
6. [Codes d'erreur](#codes-derreur)

---

## Vue d'ensemble

Cette API gère l'authentification, l'inscription et la gestion des profils utilisateurs avec un système d'authentification par OTP (One-Time Password) et JWT.

**Base URL:** `/api/auth/`

**Types d'utilisateurs:**
- `proprietaire` - Propriétaire (peut louer des biens)
- `locataire` - Locataire
- `admin` - Administrateur

---

## Authentification

L'API utilise JWT (JSON Web Tokens) avec système de refresh tokens.

### Headers requis pour les endpoints protégés
```
Authorization: Bearer <access_token>
```

---

## Endpoints Publics

### 1. Inscription d'un utilisateur

**POST** `/api/auth/register/`

Crée un nouveau compte utilisateur et envoie un OTP de vérification par email.

**Permissions:** Aucune (AllowAny)

**Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "proprietaire",
  "phone_number": "+229xxxxxxxx",
  "profile_name": "Hôtel Dallas"
}
```

**Champs obligatoires:**
- `email` (string)
- `first_name` (string)
- `last_name` (string)
- `user_type` (string: 'proprietaire' ou 'locataire')

**Champs optionnels:**
- `phone_number` (string)
- `profile_name` (string)

**Réponse (201):**
```json
{
  "message": "Inscription réussie. Un code de vérification a été envoyé à votre email.",
  "email": "user@example.com"
}
```

**Erreurs possibles:**
- 400: Email déjà utilisé
- 400: Mots de passe ne correspondent pas
- 400: Type d'utilisateur invalide

---

### 2. Envoyer un OTP

**POST** `/api/auth/send-otp/`

Génère et envoie un code OTP à 6 chiffres par email (valide 10 minutes).

**Permissions:** Aucune (AllowAny)

**Body:**
```json
{
  "email": "user@example.com",
  "purpose": "login"
}
```

**Paramètres:**
- `email` (string, required): Email de l'utilisateur
- `purpose` (string, required): 'login' ou 'register'

**Réponse (200):**
```json
{
  "message": "Code de vérification envoyé à user@example.com.",
  "expires_in": 600
}
```

**Erreurs possibles:**
- 404: Aucun compte associé à cet email
- 400: Paramètres invalides

---

### 3. Vérifier l'OTP et se connecter

**POST** `/api/auth/verify-otp/`

Vérifie le code OTP et retourne les tokens JWT d'authentification.

**Permissions:** Aucune (AllowAny)

**Body:**
```json
{
  "email": "user@example.com",
  "token": "123456",
  "device_name": "iPhone 12",
  "device_type": "mobile"
}
```

**Paramètres:**
- `email` (string, required): Email de l'utilisateur
- `token` (string, required): Code OTP à 6 chiffres
- `device_name` (string, optional): Nom de l'appareil (défaut: "Unknown Device")
- `device_type` (string, optional): Type d'appareil - 'mobile', 'desktop' ou 'tablet' (défaut: 'desktop')

**Réponse (200):**
```json
{
  "message": "Authentification réussie.",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "user_type": "proprietaire",
    "phone_number": "+229xxxxxxxx",
    "profile_name": "Hôtel Dallas",
    "is_identity_verified": false,
    "identity_verified_at": null,
    "email_verified": true,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  "session_id": 5
}
```

**Erreurs possibles:**
- 400: Utilisateur non trouvé
- 400: Code OTP invalide
- 400: Code OTP expiré

---

### 4. Rafraîchir le token d'accès

**POST** `/api/auth/refresh/`

Génère un nouveau token d'accès à partir du refresh token.

**Permissions:** Aucune (AllowAny)

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Réponse (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Erreurs possibles:**
- 400: Refresh token requis
- 401: Token invalide ou expiré

---

### 5. Connexion (alias)

**POST** `/api/auth/login/`

Alias de l'endpoint `/send-otp/` avec `purpose: "login"`.

---

## Endpoints Utilisateur

### 6. Déconnexion

**POST** `/api/auth/logout/`

Déconnecte l'utilisateur en invalidant le refresh token et la session.

**Permissions:** IsAuthenticated

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Réponse (200):**
```json
{
  "message": "Déconnexion réussie."
}
```

**Erreurs possibles:**
- 400: Refresh token requis
- 400: Token invalide
- 401: Non authentifié

---

### 7. Consulter son profil

**GET** `/api/auth/profile/`

Récupère les informations du profil de l'utilisateur connecté.

**Permissions:** IsAuthenticated

**Headers:**
```
Authorization: Bearer <access_token>
```

**Réponse (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "user_type": "proprietaire",
  "phone_number": "+229xxxxxxxx",
  "profile_name": "Hôtel Dallas",
  "is_identity_verified": true,
  "identity_verified_at": "2025-01-20T14:30:00Z",
  "email_verified": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### 8. Modifier son profil

**PATCH** `/api/auth/profile/`

Met à jour les informations du profil.

**Permissions:** IsAuthenticated

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body (tous les champs sont optionnels):**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+229xxxxxxxx",
  "profile_name": "Hôtel Dallas VIP"
}
```

**Champs modifiables:**
- `first_name` (string)
- `last_name` (string)
- `phone_number` (string)
- `profile_name` (string)

**Champs en lecture seule:**
- `email`, `user_type`, `is_identity_verified`, `identity_verified_at`, `email_verified`, `created_at`, `updated_at`

**Réponse (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "user_type": "proprietaire",
  "phone_number": "+229xxxxxxxx",
  "profile_name": "Hôtel Dallas VIP",
  "is_identity_verified": true,
  "identity_verified_at": "2025-01-20T14:30:00Z",
  "email_verified": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### 9. Uploader un document d'identité

**POST** `/api/auth/upload-identity/`

Permet aux propriétaires d'uploader leur CNI pour vérification.

**Permissions:** IsAuthenticated + IsProprietaire (uniquement les propriétaires)

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Body (form-data):**
```
identity_document: <fichier>
```

**Contraintes:**
- Formats acceptés: JPG, PNG, PDF
- Taille maximum: 5MB

**Réponse (200):**
```json
{
  "message": "Document d'identité uploadé avec succès. En attente de validation.",
  "identity_document": "/media/identities/cni_user123.jpg"
}
```

**Erreurs possibles:**
- 400: Format de fichier non autorisé
- 400: Le fichier ne doit pas dépasser 5MB
- 403: Accès refusé (uniquement pour les propriétaires)

---

### 10. Lister ses sessions actives

**GET** `/api/auth/sessions/`

Liste tous les appareils/sessions actifs de l'utilisateur.

**Permissions:** IsAuthenticated

**Headers:**
```
Authorization: Bearer <access_token>
```

**Réponse (200):**
```json
[
  {
    "id": 5,
    "device_name": "iPhone 12",
    "device_type": "mobile",
    "ip_address": "192.168.1.10",
    "is_active": true,
    "last_activity": "2025-01-20T15:45:00Z",
    "created_at": "2025-01-15T10:30:00Z",
    "is_current": true
  },
  {
    "id": 3,
    "device_name": "MacBook Pro",
    "device_type": "desktop",
    "ip_address": "192.168.1.20",
    "is_active": true,
    "last_activity": "2025-01-19T09:20:00Z",
    "created_at": "2025-01-10T14:00:00Z",
    "is_current": false
  }
]
```

---

### 11. Consulter une session spécifique

**GET** `/api/auth/sessions/{id}/`

Récupère les détails d'une session spécifique.

**Permissions:** IsAuthenticated

**Headers:**
```
Authorization: Bearer <access_token>
```

**Réponse (200):**
```json
{
  "id": 5,
  "device_name": "iPhone 12",
  "device_type": "mobile",
  "ip_address": "192.168.1.10",
  "is_active": true,
  "last_activity": "2025-01-20T15:45:00Z",
  "created_at": "2025-01-15T10:30:00Z",
  "is_current": true
}
```

---

### 12. Déconnecter un appareil

**DELETE** `/api/auth/sessions/{id}/disconnect/`

Déconnecte un appareil/session spécifique.

**Permissions:** IsAuthenticated

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "current_refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Note:** Le `current_refresh` empêche l'utilisateur de se déconnecter lui-même par erreur.

**Réponse (200):**
```json
{
  "message": "Appareil déconnecté avec succès."
}
```

**Erreurs possibles:**
- 400: Impossible de déconnecter la session actuelle
- 404: Session non trouvée

---

## Endpoints Admin

### 13. Lister tous les utilisateurs

**GET** `/api/auth/admin/users/`

Liste tous les utilisateurs avec filtres et recherche.

**Permissions:** IsAuthenticated + IsAdminUser

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `user_type` (string, optional): Filtrer par type ('proprietaire', 'locataire')
- `is_verified` (boolean, optional): Filtrer par statut de vérification ('true', 'false')
- `is_active` (boolean, optional): Filtrer par statut actif ('true', 'false')
- `search` (string, optional): Rechercher dans email, nom, prénom, profile_name

**Exemples:**
```
GET /api/auth/admin/users/?user_type=proprietaire
GET /api/auth/admin/users/?is_verified=true
GET /api/auth/admin/users/?search=hotel
GET /api/auth/admin/users/?user_type=proprietaire&is_verified=false
```

**Réponse (200):**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "user_type": "proprietaire",
    "phone_number": "+229xxxxxxxx",
    "profile_name": "Hôtel Dallas",
    "is_identity_verified": true,
    "is_active": true,
    "identity_verified_at": "2025-01-20T14:30:00Z",
    "email_verified": true,
    "sessions_count": 2,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:30:00Z"
  }
]
```

---

### 14. Consulter un utilisateur (détails)

**GET** `/api/auth/admin/users/{id}/`

Récupère tous les détails d'un utilisateur spécifique.

**Permissions:** IsAuthenticated + IsAdminUser

**Headers:**
```
Authorization: Bearer <access_token>
```

**Réponse (200):**
```json
{
  "id": 1,
  "username": "user@example.com",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "user_type": "proprietaire",
  "phone_number": "+229xxxxxxxx",
  "profile_name": "Hôtel Dallas",
  "is_identity_verified": true,
  "identity_document": "/media/identities/cni_user123.jpg",
  "identity_verified_at": "2025-01-20T14:30:00Z",
  "email_verified": true,
  "is_active": true,
  "is_staff": false,
  "date_joined": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-20T14:30:00Z",
  "sessions": [
    {
      "id": 5,
      "device_name": "iPhone 12",
      "device_type": "mobile",
      "ip_address": "192.168.1.10",
      "is_active": true,
      "last_activity": "2025-01-20T15:45:00Z",
      "created_at": "2025-01-15T10:30:00Z",
      "is_current": false
    }
  ]
}
```

---

### 15. Valider/Rejeter l'identité d'un utilisateur

**PATCH** `/api/auth/admin/users/{id}/verify_identity/`

Approuve ou rejette le document d'identité d'un propriétaire.

**Permissions:** IsAuthenticated + IsAdminUser

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "approved": true,
  "notes": "Document vérifié et conforme"
}
```

**Paramètres:**
- `approved` (boolean, required): true pour approuver, false pour rejeter
- `notes` (string, optional): Notes sur la décision

**Réponse (200):**
```json
{
  "message": "Identité validée avec succès.",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "user_type": "proprietaire",
    "phone_number": "+229xxxxxxxx",
    "profile_name": "Hôtel Dallas",
    "is_identity_verified": true,
    "identity_document": "/media/identities/cni_user123.jpg",
    "identity_verified_at": "2025-01-20T16:00:00Z",
    "email_verified": true,
    "is_active": true,
    "is_staff": false,
    "date_joined": "2025-01-15T10:30:00Z",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T16:00:00Z",
    "sessions": [...]
  }
}
```

**Note:** Un email est automatiquement envoyé à l'utilisateur pour l'informer de la décision.

**Si rejeté (approved: false):**
- `is_identity_verified` devient `false`
- `identity_verified_at` devient `null`
- `identity_document` est supprimé

---

### 16. Bloquer/Débloquer un utilisateur

**PATCH** `/api/auth/admin/users/{id}/block/`

Bloque ou débloque l'accès d'un utilisateur à la plateforme.

**Permissions:** IsAuthenticated + IsAdminUser

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "is_active": false,
  "reason": "Violation des conditions d'utilisation"
}
```

**Paramètres:**
- `is_active` (boolean, required): false pour bloquer, true pour débloquer
- `reason` (string, optional): Raison du blocage/déblocage

**Réponse (200):**
```json
{
  "message": "Utilisateur bloqué avec succès.",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "user_type": "proprietaire",
    "phone_number": "+229xxxxxxxx",
    "profile_name": "Hôtel Dallas",
    "is_identity_verified": true,
    "identity_document": "/media/identities/cni_user123.jpg",
    "identity_verified_at": "2025-01-20T14:30:00Z",
    "email_verified": true,
    "is_active": false,
    "is_staff": false,
    "date_joined": "2025-01-15T10:30:00Z",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T16:15:00Z",
    "sessions": []
  }
}
```

**Note:** 
- Un email est automatiquement envoyé à l'utilisateur
- Lors du blocage, toutes les sessions actives sont déconnectées

---

### 17. Modifier un utilisateur (Admin)

**PATCH** `/api/auth/admin/users/{id}/`

Modifie les informations d'un utilisateur.

**Permissions:** IsAuthenticated + IsAdminUser

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body (tous les champs sont optionnels):**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+229xxxxxxxx",
  "profile_name": "Hôtel Dallas",
  "is_active": true,
  "is_staff": false
}
```

---

### 18. Supprimer un utilisateur

**DELETE** `/api/auth/admin/users/{id}/`

Supprime définitivement un utilisateur.

**Permissions:** IsAuthenticated + IsAdminUser

**Headers:**
```
Authorization: Bearer <access_token>
```

**Réponse (204):** Pas de contenu

**Attention:** Cette action est irréversible!

---

## Codes d'erreur

### Codes HTTP standards

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 201 | Créé avec succès |
| 204 | Succès sans contenu |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Accès refusé |
| 404 | Ressource non trouvée |
| 500 | Erreur serveur |

### Format des erreurs

```json
{
  "error": "Message d'erreur"
}
```

ou pour les erreurs de validation:

```json
{
  "field_name": ["Message d'erreur pour ce champ"]
}
```

**Exemples:**

```json
{
  "email": ["Cet email est déjà utilisé."],
  "password": ["Ce champ est requis."]
}
```

```json
{
  "error": "Token invalide ou expiré."
}
```

---

## Notes importantes

### Sécurité
- Les mots de passe sont hashés avec l'algorithme de Django (PBKDF2)
- Les tokens JWT expirent après un certain temps (configurable)
- Les refresh tokens peuvent être blacklistés
- Les OTP sont valides pendant 10 minutes
- Les anciens OTP sont automatiquement invalidés lors de l'envoi d'un nouveau

### Sessions
- Une session est créée à chaque connexion
- Les sessions inactives peuvent être nettoyées automatiquement
- L'utilisateur peut voir et déconnecter ses sessions actives
- La déconnexion blackliste le refresh token associé

### Vérification d'identité
- Seuls les propriétaires peuvent uploader un document d'identité
- Les admins doivent manuellement valider les documents
- Les utilisateurs reçoivent un email après validation/rejet

### Emails automatiques
- Email d'OTP lors de l'inscription/connexion
- Email de notification lors de la validation/rejet d'identité
- Email de notification lors du blocage/déblocage du compte
- Les emails sont envoyés de manière asynchrone via Celery

### Permissions
- `AllowAny`: Accessible sans authentification
- `IsAuthenticated`: Requiert un token JWT valide
- `IsProprietaire`: Requiert authentification + user_type='proprietaire'
- `IsAdminUser`: Requiert authentification + is_staff=True

---

## Exemples d'utilisation

### Flux d'inscription complet

```bash
# 1. Inscription
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePass123",
    "confirm_password": "SecurePass123",
    "user_type": "proprietaire",
    "phone_number": "+229xxxxxxxx",
    "profile_name": "Hôtel Dallas"
  }'

# 2. Vérifier l'OTP reçu par email
curl -X POST http://localhost:8000/api/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "token": "123456",
    "device_name": "Chrome Browser",
    "device_type": "desktop"
  }'

# 3. Utiliser le token pour accéder au profil
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Flux de connexion

```bash
# 1. Demander un OTP
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "purpose": "login"
  }'

# 2. Vérifier l'OTP
curl -X POST http://localhost:8000/api/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "token": "654321",
    "device_name": "iPhone 12",
    "device_type": "mobile"
  }'
```

### Upload de CNI

```bash
curl -X POST http://localhost:8000/api/auth/upload-identity/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -F "identity_document=@/path/to/cni.jpg"
```

### Gestion des sessions

```bash
# Lister les sessions
curl -X GET http://localhost:8000/api/auth/sessions/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."

# Déconnecter un appareil
curl -X DELETE http://localhost:8000/api/auth/sessions/5/disconnect/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "current_refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

---

## Support

Pour toute question ou problème, contactez ASSOUMA Z. Billa.