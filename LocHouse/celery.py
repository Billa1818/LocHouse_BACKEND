import os
from celery import Celery
from celery.schedules import crontab

# Définir le module de settings Django par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LocHouse.settings')

app = Celery('LocHouse')

# Utiliser une chaîne ici signifie que le worker ne doit pas sérialiser
# l'objet de configuration lorsqu'il utilise Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charger automatiquement les tâches de tous les modules tasks.py des apps Django
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Notifications d'expiration d'abonnement - Quotidien à 9h00
    'send-subscription-expiry-notifications': {
        'task': 'core.tasks.send_subscription_expiry_notifications',
        'schedule': crontab(hour=9, minute=0),  # Tous les jours à 9h00
        'options': {
            'expires': 3600,  # Expiration après 1 heure si non exécutée
        }
    },
    
    # Calcul des statistiques quotidiennes - Tous les jours à 23h55
    'calculate-daily-analytics': {
        'task': 'core.tasks.calculate_daily_analytics',
        'schedule': crontab(hour=23, minute=55),  # Tous les jours à 23h55
        'options': {
            'expires': 3600,
        }
    },
    
    # Notifications pour nouvelles annonces approuvées - Toutes les heures
    'send-new-listing-notifications': {
        'task': 'core.tasks.send_new_listing_notifications',
        'schedule': crontab(minute=0),  # Toutes les heures à la minute 0
        'options': {
            'expires': 1800,  # Expiration après 30 minutes
        }
    },
    
    # Nettoyage des anciennes notifications - Hebdomadaire (Dimanche à 2h00)
    'cleanup-old-notifications': {
        'task': 'core.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Dimanche à 2h00
        'options': {
            'expires': 7200,  # Expiration après 2 heures
        }
    },
    
    # Résumé hebdomadaire aux propriétaires - Lundi à 9h00
    'send-weekly-stats-to-owners': {
        'task': 'core.tasks.send_weekly_stats_to_owners',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Lundi à 9h00
        'options': {
            'expires': 7200,
        }
    },
    
    # Rapport mensuel pour admins - Premier jour du mois à 8h00
    'generate-monthly-report': {
        'task': 'core.tasks.generate_monthly_report',
        'schedule': crontab(hour=8, minute=0, day_of_month=1),  # 1er du mois à 8h00
        'options': {
            'expires': 7200,
        }

        
    },
    # Notifications d'expiration d'abonnement - Quotidien à 9h00
    'send-subscription-expiry-notifications': {
        'task': 'core.tasks.send_subscription_expiry_notifications',
        'schedule': crontab(hour=9, minute=0),  # Tous les jours à 9h00
        'options': {
            'expires': 3600,  # Expiration après 1 heure si non exécutée
        }
    },
    # Calcul des statistiques quotidiennes - Tous les jours à 23h55
    'calculate-daily-analytics': {
        'task': 'core.tasks.calculate_daily_analytics',
        'schedule': crontab(hour=23, minute=55),  # Tous les jours à 23h55
        'options': {
            'expires': 3600,
        }
    },
    # Notifications pour nouvelles annonces approuvées - Toutes les heures
    'send-new-listing-notifications': {
        'task': 'core.tasks.send_new_listing_notifications',
        'schedule': crontab(minute=0),  # Toutes les heures à la minute 0
        'options': {
            'expires': 1800,  # Expiration après 30 minutes
        }
    },
    
    # Notifications pour demandes de disponibilité - Toutes les 30 minutes
    'send-availability-request-notifications': {
        'task': 'core.tasks.send_availability_request_notifications',
        'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes
        'options': {
            'expires': 900,  # Expiration après 15 minutes
        }
    },
    
    # Nettoyage des anciennes notifications - Hebdomadaire (Dimanche à 2h00)
    'cleanup-old-notifications': {
        'task': 'core.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Dimanche à 2h00
        'options': {
            'expires': 7200,  # Expiration après 2 heures
        }
    },
    
    # Résumé hebdomadaire aux propriétaires - Lundi à 9h00
    'send-weekly-stats-to-owners': {
        'task': 'core.tasks.send_weekly_stats_to_owners',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Lundi à 9h00
        'options': {
            'expires': 7200,
        }
    },
    
    # Rapport mensuel pour admins - Premier jour du mois à 8h00
    'generate-monthly-report': {
        'task': 'core.tasks.generate_monthly_report',
        'schedule': crontab(hour=8, minute=0, day_of_month=1),  # 1er du mois à 8h00
        'options': {
            'expires': 7200,
        }
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')