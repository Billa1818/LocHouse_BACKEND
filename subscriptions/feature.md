# Exemples d'intégration Frontend - PayDunya

## 🎯 Vue d'ensemble

Ce document contient des exemples de code pour intégrer les paiements PayDunya dans votre frontend.

## 📦 Installation

```bash
npm install axios
# ou
yarn add axios
```

## 🔧 Configuration API

```javascript
// src/services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
```

## 💳 Service de paiement

```javascript
// src/services/paymentService.js
import api from './api';

export const paymentService = {
  // Initier un paiement
  async initiatePayment(subscriptionId) {
    try {
      const response = await api.post('/payments/initiate/', {
        subscription: subscriptionId,
        payment_method: 'paydunya'
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Vérifier le statut d'un paiement
  async verifyPayment(paymentId) {
    try {
      const response = await api.get(`/payments/${paymentId}/verify/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Récupérer mes paiements
  async getMyPayments() {
    try {
      const response = await api.get('/payments/my_payments/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Obtenir les détails d'un paiement
  async getPaymentDetails(paymentId) {
    try {
      const response = await api.get(`/payments/${paymentId}/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
};
```

## 📱 Service d'abonnement

```javascript
// src/services/subscriptionService.js
import api from './api';

export const subscriptionService = {
  // Obtenir les plans disponibles
  async getPlans() {
    try {
      const response = await api.get('/subscription-plans/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Créer un abonnement
  async createSubscription(planId) {
    try {
      const response = await api.post('/subscriptions/', {
        plan: planId
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Obtenir l'abonnement actuel
  async getCurrentSubscription() {
    try {
      const response = await api.get('/subscriptions/current/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Obtenir le statut complet
  async getSubscriptionStatus() {
    try {
      const response = await api.get('/subscriptions/status/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Annuler un abonnement
  async cancelSubscription(subscriptionId) {
    try {
      const response = await api.post(`/subscriptions/${subscriptionId}/cancel/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
};
```

## 🎨 Composant React - Sélection de plan

```jsx
// src/components/SubscriptionPlans.jsx
import React, { useState, useEffect } from 'react';
import { subscriptionService } from '../services/subscriptionService';
import { paymentService } from '../services/paymentService';

const SubscriptionPlans = () => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const data = await subscriptionService.getPlans();
      setPlans(data);
    } catch (err) {
      setError('Erreur lors du chargement des plans');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (plan) => {
    setLoading(true);
    setError(null);

    try {
      // 1. Créer l'abonnement
      const subscription = await subscriptionService.createSubscription(plan.id);
      
      // 2. Initier le paiement
      const payment = await paymentService.initiatePayment(subscription.id);
      
      // 3. Rediriger vers PayDunya
      window.location.href = payment.payment_url;
      
    } catch (err) {
      setError(err.error || 'Erreur lors de la souscription');
      console.error(err);
      setLoading(false);
    }
  };

  if (loading && plans.length === 0) {
    return <div className="text-center py-8">Chargement...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-8">
        Choisissez votre plan
      </h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className="border rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow"
          >
            <h2 className="text-2xl font-bold mb-2">{plan.name}</h2>
            <p className="text-gray-600 mb-4">{plan.description}</p>
            
            <div className="mb-4">
              <span className="text-4xl font-bold">{plan.price}</span>
              <span className="text-gray-600"> FCFA</span>
              <span className="text-gray-500"> / {plan.duration_months} mois</span>
            </div>

            <ul className="mb-6 space-y-2">
              <li className="flex items-center">
                <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                {plan.max_listings === -1 ? 'Annonces illimitées' : `${plan.max_listings} annonces`}
              </li>
              {plan.features?.map((feature, index) => (
                <li key={index} className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleSubscribe(plan)}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded transition-colors disabled:bg-gray-400"
            >
              {loading ? 'Chargement...' : 'Souscrire'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SubscriptionPlans;
```

## ✅ Composant React - Confirmation de paiement

```jsx
// src/components/PaymentSuccess.jsx
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { paymentService } from '../services/paymentService';

const PaymentSuccess = () => {
  const { paymentId } = useParams();
  const navigate = useNavigate();
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    verifyPayment();
  }, [paymentId]);

  const verifyPayment = async () => {
    try {
      // Vérifier le paiement auprès du serveur
      const data = await paymentService.verifyPayment(paymentId);
      setPayment(data);
      
      // Si le paiement est complété, rediriger après 3 secondes
      if (data.paydunya_status === 'completed') {
        setTimeout(() => {
          navigate('/dashboard');
        }, 3000);
      }
    } catch (err) {
      setError('Erreur lors de la vérification du paiement');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Vérification du paiement...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-md mx-auto bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded">
          <h2 className="text-xl font-bold mb-2">Erreur</h2>
          <p>{error}</p>
          <button
            onClick={() => navigate('/subscriptions')}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retour aux abonnements
          </button>
        </div>
      </div>
    );
  }

  const isCompleted = payment?.paydunya_status === 'completed';

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          {isCompleted ? (
            <>
              <svg className="w-16 h-16 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h2 className="text-2xl font-bold text-green-600 mb-2">
                Paiement confirmé !
              </h2>
              <p className="text-gray-600 mb-6">
                Votre abonnement est maintenant actif.
              </p>
            </>
          ) : (
            <>
              <svg className="w-16 h-16 text-yellow-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h2 className="text-2xl font-bold text-yellow-600 mb-2">
                Paiement en cours
              </h2>
              <p className="text-gray-600 mb-6">
                Votre paiement est en cours de traitement.
              </p>
            </>
          )}

          <div className="bg-gray-100 rounded p-4 mb-6 text-left">
            <p className="text-sm text-gray-600 mb-1">ID de transaction</p>
            <p className="font-mono text-sm">{payment?.payment_id}</p>
          </div>

          {isCompleted && (
            <p className="text-sm text-gray-500 mb-4">
              Redirection vers le tableau de bord...
            </p>
          )}

          <button
            onClick={() => navigate('/dashboard')}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded"
          >
            Aller au tableau de bord
          </button>
        </div>
      </div>
    </div>
  );
};

export default PaymentSuccess;
```

## 📊 Composant React - Statut de l'abonnement

```jsx
// src/components/SubscriptionStatus.jsx
import React, { useEffect, useState } from 'react';
import { subscriptionService } from '../services/subscriptionService';

const SubscriptionStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await subscriptionService.getSubscriptionStatus();
      setStatus(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Chargement...</div>;
  }

  if (!status?.has_active_subscription) {
    return (
      <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
        <p>Vous n'avez pas d'abonnement actif.</p>
        <a href="/subscriptions" className="underline">Souscrire maintenant</a>
      </div>
    );
  }

  const subscription = status.current_subscription;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-bold mb-4">Votre abonnement</h3>
      
      <div className="space-y-3">
        <div>
          <span className="text-gray-600">Plan:</span>
          <span className="ml-2 font-semibold">{subscription.plan.name}</span>
        </div>

        <div>
          <span className="text-gray-600">Statut:</span>
          <span className={`ml-2 px-2 py-1 rounded text-sm ${
            subscription.status === 'active' ? 'bg-green-100 text-green-800' :
            subscription.status === 'trial' ? 'bg-blue-100 text-blue-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {subscription.status === 'active' ? 'Actif' :
             subscription.status === 'trial' ? 'Période d\'essai' :
             subscription.status}
          </span>
        </div>

        <div>
          <span className="text-gray-600">Expire le:</span>
          <span className="ml-2 font-semibold">
            {new Date(subscription.end_date).toLocaleDateString('fr-FR')}
          </span>
          <span className="ml-2 text-sm text-gray-500">
            ({status.days_remaining} jours restants)
          </span>
        </div>

        <div>
          <span className="text-gray-600">Annonces:</span>
          <span className="ml-2 font-semibold">
            {status.remaining_listings === -1 
              ? 'Illimité' 
              : `${status.remaining_listings} restantes`}
          </span>
        </div>

        {status.days_remaining <= 7 && (
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded p-3">
            <p className="text-sm text-yellow-800">
              ⚠️ Votre abonnement expire bientôt. Pensez à le renouveler.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionStatus;
```

## 🔔 Service de notifications

```javascript
// src/services/notificationService.js
import api from './api';

export const notificationService = {
  // Récupérer les notifications
  async getNotifications() {
    try {
      const response = await api.get('/notifications/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Marquer comme lu
  async markAsRead(notificationId) {
    try {
      const response = await api.patch(`/notifications/${notificationId}/`, {
        is_read: true
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Marquer toutes comme lues
  async markAllAsRead() {
    try {
      const response = await api.post('/notifications/mark_all_read/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
};
```

## 🚀 Routes React Router

```jsx
// src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SubscriptionPlans from './components/SubscriptionPlans';
import PaymentSuccess from './components/PaymentSuccess';
import PaymentCancel from './components/PaymentCancel';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/subscriptions" element={<SubscriptionPlans />} />
        <Route path="/payment/success/:paymentId" element={<PaymentSuccess />} />
        <Route path="/payment/cancel/:paymentId" element={<PaymentCancel />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

## 📱 Gestion d'erreurs

```javascript
// src/utils/errorHandler.js
export const handleApiError = (error) => {
  if (error.response) {
    // Erreur de réponse du serveur
    const status = error.response.status;
    const data = error.response.data;

    if (status === 401) {
      // Non authentifié - rediriger vers login
      window.location.href = '/login';
      return 'Session expirée. Veuillez vous reconnecter.';
    }

    if (status === 403) {
      return 'Vous n\'avez pas les permissions nécessaires.';
    }

    if (status === 404) {
      return 'Ressource introuvable.';
    }

    if (data.error) {
      return data.error;
    }

    if (data.detail) {
      return data.detail;
    }

    return 'Une erreur est survenue.';
  }

  if (error.request) {
    // Pas de réponse du serveur
    return 'Impossible de contacter le serveur.';
  }

  // Autre erreur
  return error.message || 'Une erreur inattendue est survenue.';
};
```

## 🎯 Utilisation

```jsx
import { handleApiError } from './utils/errorHandler';
import { paymentService } from './services/paymentService';

const handlePayment = async () => {
  try {
    const result = await paymentService.initiatePayment(subscriptionId);
    // Succès
  } catch (error) {
    const errorMessage = handleApiError(error);
    setError(errorMessage);
  }
};
```