# ============================================================================
# ENDPOINTS - accounts
# ============================================================================

"""
POST   /api/auth/register/                    - Inscription (email, nom, prénom, type)
POST   /api/auth/send-otp/                    - Envoyer OTP par email
POST   /api/auth/verify-otp/                  - Vérifier OTP et obtenir JWT tokens
POST   /api/auth/login/                       - Connexion (envoie OTP)
POST   /api/auth/refresh/                     - Rafraîchir access token
POST   /api/auth/logout/                      - Déconnexion (invalide refresh token)

GET    /api/auth/profile/                     - Profil utilisateur connecté
PATCH  /api/auth/profile/                     - Modifier profil
POST   /api/auth/upload-identity/             - Upload CNI (propriétaires)
GET    /api/auth/sessions/                    - Liste des sessions actives
DELETE /api/auth/sessions/{id}/               - Déconnecter un appareil

# ADMIN
GET    /api/admin/users/                      - Liste utilisateurs
PATCH  /api/admin/users/{id}/verify-identity/ - Valider identité
PATCH  /api/admin/users/{id}/block/           - Bloquer utilisateur
"""

"""

## 7. Tester les endpoints

### Inscription
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "motdepasse123",
    "confirm_password": "motdepasse123",
    "user_type": "proprietaire"
  }'
```

### Vérifier OTP
```bash
curl -X POST http://localhost:8000/api/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "token": "123456",
    "device_name": "Mon iPhone",
    "device_type": "mobile"
  }'
```

### Accéder au profil
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Upload CNI (propriétaires)
```bash
curl -X POST http://localhost:8000/api/auth/upload-identity/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "identity_document=@/path/to/cni.jpg"
```

### Liste des sessions
```bash
curl -X GET http://localhost:8000/api/auth/sessions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Déconnecter un appareil
```bash
curl -X DELETE http://localhost:8000/api/auth/sessions/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 8. Endpoints Admin

### Liste utilisateurs
```bash
curl -X GET "http://localhost:8000/api/admin/users/?user_type=proprietaire&is_verified=false" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### Valider identité
```bash
curl -X PATCH http://localhost:8000/api/admin/users/1/verify_identity/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "notes": "Document valide"
  }'
```

### Bloquer utilisateur
```bash
curl -X PATCH http://localhost:8000/api/admin/users/1/block/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false,
    "reason": "Violation des CGU"
  }'
```

## 9. Structure des fichiers

```
accounts/
├── __init__.py
├── models.py           # Déjà fourni
├── serializers.py      # Créé
├── views.py            # Créé
├── urls.py             # Créé
├── permissions.py      # Créé
├── admin.py           # À créer pour Django admin
└── tests.py           # À créer pour les tests

core/
└── urls.py            # Créé - Routes admin
```

## 10. Notes importantes

### Sécurité
- Les mots de passe sont automatiquement hachés par Django
- Les tokens JWT expirent après 30 minutes (access) et 7 jours (refresh)
- Les OTP expirent après 10 minutes
- Les documents d'identité sont stockés dans le dossier `media/identities/`

### Email
- Assurez-vous que la configuration email est correcte
- Pour Gmail, utilisez un "mot de passe d'application"
- En développement, vous pouvez utiliser `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` pour afficher les emails dans la console

### Sessions
- Les sessions inactives restent valides tant que le refresh token n'a pas expiré
- Un utilisateur peut avoir plusieurs sessions actives simultanément
- La déconnexion d'un appareil blackliste le refresh token associé

### Permissions
- Les propriétaires doivent être vérifiés pour certaines actions (à définir selon vos besoins)
- Les locataires ont une inscription simplifiée sans vérification d'identité
- Les admins ont accès à tous les endpoints d'administration

"""