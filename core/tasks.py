# core/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification, Analytics
from accounts.models import User
from subscriptions.models import Subscription, Payment
from listings.models import Listing, PropertyGroup
from interactions.models import Review, AvailabilityRequest


@shared_task
def send_subscription_expiry_notifications():
    """
    Tâche pour envoyer des notifications d'expiration d'abonnement
    EF-A-05: Envoi de rappels automatiques d'expiration
    
    Exécution recommandée: Quotidienne à 9h00
    """
    today = timezone.now().date()
    
    # Notifications pour abonnements expirant dans 7 jours
    expiring_in_7_days = timezone.now() + timedelta(days=7)
    subscriptions_7_days = Subscription.objects.filter(
        status='active',
        end_date__date=expiring_in_7_days.date()
    ).select_related('user', 'plan')
    
    count_7_days = 0
    for subscription in subscriptions_7_days:
        # Créer notification dans l'app
        Notification.objects.create(
            user=subscription.user,
            notification_type='subscription_expiring',
            title='Votre abonnement expire dans 7 jours',
            message=f'Votre abonnement {subscription.plan.name} expire le {subscription.end_date.strftime("%d/%m/%Y")}. Renouvelez maintenant pour continuer à profiter de vos avantages.',
            link=f'/dashboard/subscriptions/{subscription.id}/renew'
        )
        
        # Envoyer email (notification critique - toujours envoyée)
        try:
            send_mail(
                subject='⚠️ Votre abonnement LocHouse expire bientôt',
                message=f'Bonjour {subscription.user.get_full_name()},\n\n'
                        f'Votre abonnement {subscription.plan.name} expire dans 7 jours (le {subscription.end_date.strftime("%d/%m/%Y")}).\n\n'
                        f'Renouvelez dès maintenant pour continuer à bénéficier de tous vos avantages.\n\n'
                        f'Cordialement,\nL\'équipe LocHouse',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.user.email],
                fail_silently=True,
            )
            count_7_days += 1
        except Exception as e:
            print(f"Erreur envoi email pour {subscription.user.email}: {e}")
    
    # Notifications pour abonnements expirant dans 3 jours
    expiring_in_3_days = timezone.now() + timedelta(days=3)
    subscriptions_3_days = Subscription.objects.filter(
        status='active',
        end_date__date=expiring_in_3_days.date()
    ).select_related('user', 'plan')
    
    count_3_days = 0
    for subscription in subscriptions_3_days:
        Notification.objects.create(
            user=subscription.user,
            notification_type='subscription_expiring',
            title='⚠️ Votre abonnement expire dans 3 jours !',
            message=f'URGENT: Votre abonnement expire le {subscription.end_date.strftime("%d/%m/%Y")}. Renouvelez maintenant pour éviter l\'interruption de service.',
            link=f'/dashboard/subscriptions/{subscription.id}/renew'
        )
        
        try:
            send_mail(
                subject='🚨 URGENT: Votre abonnement LocHouse expire dans 3 jours',
                message=f'Bonjour {subscription.user.get_full_name()},\n\n'
                        f'ATTENTION: Votre abonnement expire dans 3 jours (le {subscription.end_date.strftime("%d/%m/%Y")}).\n\n'
                        f'Après cette date, vos annonces ne seront plus visibles.\n\n'
                        f'Renouvelez immédiatement: {settings.SITE_URL}/dashboard/subscriptions/{subscription.id}/renew\n\n'
                        f'Cordialement,\nL\'équipe LocHouse',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.user.email],
                fail_silently=True,
            )
            count_3_days += 1
        except Exception as e:
            print(f"Erreur envoi email pour {subscription.user.email}: {e}")
    
    # Notifications pour abonnements expirés aujourd'hui
    expired_today = Subscription.objects.filter(
        status='active',
        end_date__date=today
    ).select_related('user', 'plan')
    
    count_expired = 0
    for subscription in expired_today:
        # Mettre à jour le statut
        subscription.status = 'expired'
        subscription.save()
        
        Notification.objects.create(
            user=subscription.user,
            notification_type='subscription_expiring',
            title='Votre abonnement a expiré',
            message=f'Votre abonnement a expiré aujourd\'hui. Vos annonces sont maintenant désactivées. Renouvelez pour les réactiver.',
            link=f'/dashboard/subscriptions/{subscription.id}/renew'
        )
        
        try:
            send_mail(
                subject='Votre abonnement LocHouse a expiré',
                message=f'Bonjour {subscription.user.get_full_name()},\n\n'
                        f'Votre abonnement a expiré aujourd\'hui.\n\n'
                        f'Vos annonces ne sont plus visibles sur la plateforme.\n\n'
                        f'Renouvelez maintenant: {settings.SITE_URL}/dashboard/subscriptions/renew\n\n'
                        f'Cordialement,\nL\'équipe LocHouse',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.user.email],
                fail_silently=True,
            )
            count_expired += 1
        except Exception as e:
            print(f"Erreur envoi email pour {subscription.user.email}: {e}")
    
    return {
        'expiring_in_7_days': count_7_days,
        'expiring_in_3_days': count_3_days,
        'expired_today': count_expired,
        'total_notifications_sent': count_7_days + count_3_days + count_expired
    }


@shared_task
def calculate_daily_analytics():
    """
    Tâche pour calculer les statistiques quotidiennes
    EF-A-08: Reporting et Statistiques
    
    Exécution recommandée: Quotidienne à 23h55
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Vérifier si les stats du jour existent déjà
    analytics, created = Analytics.objects.get_or_create(
        date=yesterday,
        defaults={
            'new_users': 0,
            'new_listings': 0,
            'active_subscriptions': 0,
            'revenue': 0,
            'total_searches': 0,
            'total_contacts': 0,
        }
    )
    
    # Nouveaux utilisateurs inscrits hier
    new_users = User.objects.filter(
        date_joined__date=yesterday
    ).count()
    
    # Nouvelles annonces créées hier
    new_listings = Listing.objects.filter(
        created_at__date=yesterday
    ).count()
    
    # Abonnements actifs au moment du calcul
    active_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__gte=timezone.now()
    ).count()
    
    # Revenus générés hier (paiements complétés)
    revenue = Payment.objects.filter(
        status='completed',
        paid_at__date=yesterday
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Nombre de recherches effectuées (à implémenter avec un tracking)
    total_searches = 0  # À implémenter avec un système de tracking
    
    # Nombre de demandes de disponibilité (contacts) établis hier
    total_contacts = AvailabilityRequest.objects.filter(
        created_at__date=yesterday
    ).count()
    
    # Mettre à jour les statistiques
    analytics.new_users = new_users
    analytics.new_listings = new_listings
    analytics.active_subscriptions = active_subscriptions
    analytics.revenue = revenue
    analytics.total_searches = total_searches
    analytics.total_contacts = total_contacts
    analytics.save()
    
    return {
        'date': str(yesterday),
        'new_users': new_users,
        'new_listings': new_listings,
        'active_subscriptions': active_subscriptions,
        'revenue': float(revenue),
        'total_contacts': total_contacts,
        'created': created
    }


@shared_task
def send_new_listing_notifications():
    """
    Notifier les propriétaires des nouvelles annonces approuvées
    
    Exécution recommandée: Toutes les heures
    """
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    # Récupérer les annonces publiées dans la dernière heure
    new_listings = Listing.objects.filter(
        status='published',
        published_at__gte=one_hour_ago
    ).select_related('owner', 'property_group')
    
    notifications_sent = 0
    for listing in new_listings:
        # Notifier le propriétaire
        Notification.objects.create(
            user=listing.owner,
            notification_type='listing_approved',
            title='✅ Votre annonce a été approuvée !',
            message=f'Votre annonce "{listing.title}" est maintenant visible sur la plateforme.',
            link=f'/listings/{listing.id}'
        )
        
        # Envoyer email au propriétaire
        try:
            send_mail(
                subject='✅ Votre annonce LocHouse a été approuvée',
                message=f'Bonjour {listing.owner.get_full_name()},\n\n'
                        f'Bonne nouvelle ! Votre annonce "{listing.title}" a été approuvée.\n\n'
                        f'Elle est maintenant visible par tous les utilisateurs de LocHouse.\n\n'
                        f'Voir l\'annonce: {settings.SITE_URL}/listings/{listing.id}\n\n'
                        f'Cordialement,\nL\'équipe LocHouse',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[listing.owner.email],
                fail_silently=True,
            )
            notifications_sent += 1
        except Exception as e:
            print(f"Erreur envoi email pour listing {listing.id}: {e}")
    
    return {
        'new_approved_listings': new_listings.count(),
        'notifications_sent': notifications_sent
    }


@shared_task
def send_availability_request_notifications():
    """
    Notifier les propriétaires des nouvelles demandes de disponibilité non traitées
    Respecte les préférences de notifications des groupes de propriétés
    
    Exécution recommandée: Toutes les 30 minutes
    """
    thirty_minutes_ago = timezone.now() - timedelta(minutes=30)
    
    # Récupérer les demandes non notifiées
    new_requests = AvailabilityRequest.objects.filter(
        owner_notified=False,
        created_at__gte=thirty_minutes_ago
    ).select_related('listing', 'listing__owner', 'listing__property_group', 'requester')
    
    notifications_sent = 0
    for request in new_requests:
        listing = request.listing
        
        # Vérifier si les notifications sont activées pour ce groupe
        if listing.property_group and not listing.property_group.notifications_enabled:
            # Marquer comme notifié même si on n'envoie pas (pour ne pas redemander)
            request.owner_notified = True
            request.save()
            continue
        
        # Créer notification
        Notification.objects.create(
            user=listing.owner,
            notification_type='new_availability_request',
            title=f'📧 Nouvelle demande pour {listing.title}',
            message=f'{request.requester.get_full_name()} est intéressé par votre bien. Contactez-le au {request.requester_phone}.',
            link=f'/dashboard/requests/{request.id}'
        )
        
        # Envoyer email
        try:
            send_mail(
                subject=f'📧 Nouvelle demande de disponibilité - {listing.title}',
                message=f'Bonjour {listing.owner.get_full_name()},\n\n'
                        f'Vous avez reçu une nouvelle demande pour "{listing.title}".\n\n'
                        f'Client: {request.requester.get_full_name()}\n'
                        f'Téléphone: {request.requester_phone}\n'
                        f'Nombre de personnes: {request.guests_count}\n'
                        f'Message: {request.message}\n\n'
                        f'Voir les détails: {settings.SITE_URL}/dashboard/requests/{request.id}\n\n'
                        f'Cordialement,\nL\'équipe LocHouse',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[listing.owner.email],
                fail_silently=True,
            )
            notifications_sent += 1
        except Exception as e:
            print(f"Erreur envoi email pour request {request.id}: {e}")
        
        # Marquer comme notifié
        request.owner_notified = True
        request.save()
    
    return {
        'new_requests': new_requests.count(),
        'notifications_sent': notifications_sent
    }


@shared_task
def cleanup_old_notifications():
    """
    Nettoyer les anciennes notifications lues (> 30 jours)
    
    Exécution recommandée: Hebdomadaire (dimanche à 2h00)
    """
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=thirty_days_ago
    ).delete()
    
    return {
        'deleted_notifications': deleted_count,
        'cutoff_date': str(thirty_days_ago.date())
    }


@shared_task
def send_weekly_stats_to_owners():
    """
    Envoyer un résumé hebdomadaire aux propriétaires
    
    Exécution recommandée: Lundi à 9h00
    """
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    owners = User.objects.filter(
        user_type='proprietaire',
        is_active=True
    ).prefetch_related('property_groups', 'listings')
    
    emails_sent = 0
    for owner in owners:
        # Calculer les stats de la semaine
        total_views = 0  # À implémenter avec tracking
        
        new_requests = AvailabilityRequest.objects.filter(
            listing__owner=owner,
            created_at__gte=seven_days_ago
        ).count()
        
        new_reviews = Review.objects.filter(
            listing__owner=owner,
            created_at__gte=seven_days_ago
        ).count()
        
        # Envoyer seulement s'il y a de l'activité
        if new_requests > 0 or new_reviews > 0:
            try:
                send_mail(
                    subject='📊 Votre résumé hebdomadaire LocHouse',
                    message=f'Bonjour {owner.get_full_name()},\n\n'
                            f'Voici votre résumé de la semaine:\n\n'
                            f'📧 Nouvelles demandes: {new_requests}\n'
                            f'⭐ Nouveaux avis: {new_reviews}\n\n'
                            f'Consultez votre tableau de bord: {settings.SITE_URL}/dashboard\n\n'
                            f'Cordialement,\nL\'équipe LocHouse',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[owner.email],
                    fail_silently=True,
                )
                emails_sent += 1
            except Exception as e:
                print(f"Erreur envoi email pour owner {owner.id}: {e}")
    
    return {
        'owners_notified': emails_sent,
        'period': 'last_7_days'
    }


@shared_task
def generate_monthly_report():
    """
    Générer un rapport mensuel pour les administrateurs
    
    Exécution recommandée: Premier jour du mois à 8h00
    """
    today = timezone.now().date()
    first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_day_last_month = today.replace(day=1) - timedelta(days=1)
    
    # Agréger les données du mois précédent
    monthly_analytics = Analytics.objects.filter(
        date__gte=first_day_last_month,
        date__lte=last_day_last_month
    ).aggregate(
        total_new_users=Sum('new_users'),
        total_new_listings=Sum('new_listings'),
        total_revenue=Sum('revenue'),
        total_contacts=Sum('total_contacts')
    )
    
    # Envoyer rapport aux admins
    admin_emails = User.objects.filter(
        is_staff=True,
        is_active=True
    ).values_list('email', flat=True)
    
    if admin_emails:
        report_message = f"""
Rapport Mensuel LocHouse - {first_day_last_month.strftime('%B %Y')}

📊 STATISTIQUES GLOBALES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 Nouveaux utilisateurs: {monthly_analytics['total_new_users'] or 0}
🏠 Nouvelles annonces: {monthly_analytics['total_new_listings'] or 0}
💰 Revenus générés: {monthly_analytics['total_revenue'] or 0} FCFA
📧 Demandes établies: {monthly_analytics['total_contacts'] or 0}

📅 Période: {first_day_last_month.strftime('%d/%m/%Y')} - {last_day_last_month.strftime('%d/%m/%Y')}

Consultez le dashboard complet: {settings.SITE_URL}/admin/analytics/dashboard

Cordialement,
Système LocHouse
        """
        
        try:
            send_mail(
                subject=f'📊 Rapport Mensuel LocHouse - {first_day_last_month.strftime("%B %Y")}',
                message=report_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(admin_emails),
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur envoi rapport mensuel: {e}")
    
    return {
        'month': first_day_last_month.strftime('%B %Y'),
        'total_new_users': monthly_analytics['total_new_users'] or 0,
        'total_new_listings': monthly_analytics['total_new_listings'] or 0,
        'total_revenue': float(monthly_analytics['total_revenue'] or 0),
        'total_contacts': monthly_analytics['total_contacts'] or 0,
        'admins_notified': len(admin_emails)
    }



@shared_task
def cleanup_expired_property_groups():
    """
    Nettoie les PropertyGroup des utilisateurs dont l'essai gratuit ou l'abonnement a expiré
    
    Règles de suppression:
    - Utilisateurs sans abonnement actif ET inscription > 30 jours
    - Utilisateurs avec abonnement expiré
    
    Exécution recommandée: Quotidienne à 2h00
    """
    from django.utils import timezone
    from datetime import timedelta
    from accounts.models import User
    from listings.models import PropertyGroup
    from subscriptions.models import Subscription
    
    FREE_TRIAL_DAYS = 30
    today = timezone.now()
    trial_expiry_date = today - timedelta(days=FREE_TRIAL_DAYS)
    
    deleted_counts = {
        'trial_expired': 0,
        'subscription_expired': 0,
        'total_groups_deleted': 0,
        'users_affected': 0
    }
    
    # 1. Nettoyer les PropertyGroup des utilisateurs avec essai gratuit expiré
    #    (propriétaires inscrits depuis plus de 30 jours sans abonnement actif)
    
    trial_expired_users = User.objects.filter(
        user_type='proprietaire',
        created_at__lt=trial_expiry_date,
        is_active=True
    ).exclude(
        subscriptions__status='active',
        subscriptions__end_date__gt=today
    )
    
    for user in trial_expired_users:
        # Vérifier qu'il n'a vraiment aucun abonnement actif
        has_active_sub = Subscription.objects.filter(
            user=user,
            status='active',
            end_date__gt=today
        ).exists()
        
        if not has_active_sub:
            count = PropertyGroup.objects.filter(owner=user).count()
            if count > 0:
                PropertyGroup.objects.filter(owner=user).delete()
                deleted_counts['trial_expired'] += count
                deleted_counts['users_affected'] += 1
                
                # Créer notification pour l'utilisateur
                from core.models import Notification
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title='⚠️ Groupes de propriétés supprimés',
                    message=f'Votre période d\'essai gratuit de 30 jours est expirée. '
                           f'{count} groupe(s) de propriétés ont été supprimés. '
                           f'Souscrivez à un abonnement pour créer des groupes illimités.',
                    link='/dashboard/subscriptions'
                )
    
    # 2. Nettoyer les PropertyGroup des utilisateurs avec abonnement expiré
    
    expired_subscriptions = Subscription.objects.filter(
        status='expired',
        end_date__lt=today
    ).select_related('user')
    
    for subscription in expired_subscriptions:
        user = subscription.user
        
        # Vérifier qu'il n'a pas d'autre abonnement actif
        has_active_sub = Subscription.objects.filter(
            user=user,
            status='active',
            end_date__gt=today
        ).exists()
        
        if not has_active_sub:
            count = PropertyGroup.objects.filter(owner=user).count()
            if count > 0:
                PropertyGroup.objects.filter(owner=user).delete()
                deleted_counts['subscription_expired'] += count
                
                # Vérifier si déjà comptabilisé dans trial_expired
                if user not in [u for u in trial_expired_users]:
                    deleted_counts['users_affected'] += 1
                
                # Créer notification
                from core.models import Notification
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title='⚠️ Abonnement expiré - Groupes supprimés',
                    message=f'Votre abonnement a expiré. '
                           f'{count} groupe(s) de propriétés ont été supprimés. '
                           f'Renouvelez votre abonnement pour retrouver tous vos avantages.',
                    link='/dashboard/subscriptions/renew'
                )
    
    deleted_counts['total_groups_deleted'] = (
        deleted_counts['trial_expired'] + 
        deleted_counts['subscription_expired']
    )
    
    return deleted_counts