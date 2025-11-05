from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from .models import Subscription
from core.models import Notification


@shared_task
def check_expiring_subscriptions():
    """
    Tâche quotidienne pour vérifier les abonnements qui expirent bientôt
    et envoyer des notifications aux utilisateurs.
    """
    now = timezone.now()
    
    # Dates de notification: 7 jours, 3 jours, 1 jour avant expiration
    warning_dates = [
        now + timedelta(days=7),
        now + timedelta(days=3),
        now + timedelta(days=1)
    ]
    
    for days_before in [7, 3, 1]:
        target_date = now + timedelta(days=days_before)
        
        # Trouver les abonnements qui expirent à cette date
        expiring_subscriptions = Subscription.objects.filter(
            status__in=['trial', 'active'],
            end_date__date=target_date.date(),
            auto_renew=False  # Seulement ceux qui ne se renouvellent pas automatiquement
        )
        
        for subscription in expiring_subscriptions:
            # Vérifier si on a déjà envoyé une notification pour cette échéance
            existing_notification = Notification.objects.filter(
                user=subscription.user,
                notification_type='subscription_expiring',
                created_at__gte=now - timedelta(hours=23),  # Dans les dernières 24h
                message__contains=f"{days_before} jour"
            ).exists()
            
            if not existing_notification:
                # Créer la notification
                if days_before == 1:
                    message = f"Votre abonnement {subscription.plan.name} expire demain. Pensez à le renouveler pour continuer à profiter de nos services."
                else:
                    message = f"Votre abonnement {subscription.plan.name} expire dans {days_before} jours. Pensez à le renouveler pour continuer à profiter de nos services."
                
                Notification.objects.create(
                    user=subscription.user,
                    notification_type='subscription_expiring',
                    title=f'Abonnement expire dans {days_before} jour{"s" if days_before > 1 else ""}',
                    message=message,
                    link=f'/subscriptions/{subscription.id}'
                )
    
    return f"Vérification des abonnements expirants terminée"


@shared_task
def expire_subscriptions():
    """
    Tâche quotidienne pour marquer comme expirés les abonnements dont la date de fin est dépassée.
    """
    now = timezone.now()
    
    # Trouver tous les abonnements actifs ou en période d'essai qui sont expirés
    expired_subscriptions = Subscription.objects.filter(
        Q(status='active') | Q(status='trial'),
        end_date__lt=now
    )
    
    count = 0
    for subscription in expired_subscriptions:
        subscription.status = 'expired'
        subscription.auto_renew = False
        subscription.save()
        
        # Notification d'expiration
        Notification.objects.create(
            user=subscription.user,
            notification_type='subscription_expiring',
            title='Abonnement expiré',
            message=f"Votre abonnement {subscription.plan.name} a expiré. Renouvelez-le pour continuer à utiliser nos services.",
            link=f'/subscriptions/{subscription.id}'
        )
        
        count += 1
    
    return f"{count} abonnement(s) marqué(s) comme expiré(s)"


@shared_task
def auto_renew_subscriptions():
    """
    Tâche quotidienne pour renouveler automatiquement les abonnements avec auto_renew=True.
    Note: Cette fonction crée un nouvel abonnement en attente de paiement.
    Dans un système de production, vous devriez intégrer un système de paiement récurrent.
    """
    from dateutil.relativedelta import relativedelta
    
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    
    # Trouver les abonnements qui expirent demain et ont auto_renew activé
    subscriptions_to_renew = Subscription.objects.filter(
        status__in=['active', 'trial'],
        end_date__date=tomorrow.date(),
        auto_renew=True
    )
    
    count = 0
    for old_subscription in subscriptions_to_renew:
        # Créer un nouvel abonnement
        start_date = old_subscription.end_date
        end_date = start_date + relativedelta(months=old_subscription.plan.duration_months)
        
        new_subscription = Subscription.objects.create(
            user=old_subscription.user,
            plan=old_subscription.plan,
            status='pending',  # En attente de paiement
            start_date=start_date,
            end_date=end_date,
            is_trial=False,
            auto_renew=True
        )
        
        # Notification de renouvellement
        Notification.objects.create(
            user=old_subscription.user,
            notification_type='subscription_expiring',
            title='Renouvellement automatique en cours',
            message=f"Votre abonnement {old_subscription.plan.name} est en cours de renouvellement. Veuillez procéder au paiement.",
            link=f'/subscriptions/{new_subscription.id}'
        )
        
        count += 1
    
    return f"{count} abonnement(s) programmé(s) pour renouvellement automatique"


