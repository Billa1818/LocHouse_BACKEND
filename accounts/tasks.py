from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_otp_email_task(self, user_id, otp_token, user_full_name):
    """
    Tâche asynchrone pour envoyer un OTP par email
    """
    logger.info(f"Début de l'envoi d'OTP pour l'utilisateur ID: {user_id}")
    
    try:
        subject = "Votre code de vérification LocHouse"
        message = f"""
Bonjour {user_full_name},

Votre code de vérification est: {otp_token}

Ce code expire dans 10 minutes.

Si vous n'avez pas demandé ce code, ignorez ce message.

Cordialement,
L'équipe LocHouse
        """
        
        user = User.objects.get(id=user_id)
        logger.debug(f"Utilisateur trouvé: {user.email}")
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"OTP envoyé avec succès à {user.email} (User ID: {user_id})")
        return f"OTP envoyé avec succès à {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur avec l'ID {user_id} n'existe pas")
        raise
    except Exception as exc:
        logger.warning(
            f"Échec de l'envoi d'OTP pour l'utilisateur ID: {user_id}. "
            f"Tentative {self.request.retries + 1}/{self.max_retries}. "
            f"Erreur: {str(exc)}"
        )
        # Retry après 60 secondes en cas d'échec
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_identity_verification_email_task(self, user_id, approved, notes=''):
    """
    Tâche asynchrone pour envoyer un email de validation/rejet d'identité
    """
    status = "approuvée" if approved else "rejetée"
    logger.info(f"Début de l'envoi d'email de vérification d'identité ({status}) pour l'utilisateur ID: {user_id}")
    
    try:
        user = User.objects.get(id=user_id)
        logger.debug(f"Utilisateur trouvé: {user.email}")
        
        if approved:
            subject = 'Identité vérifiée - LocHouse'
            message = f"""
Bonjour {user.get_full_name()},

Votre identité a été vérifiée avec succès. Vous pouvez maintenant profiter de toutes les fonctionnalités de LocHouse.

Cordialement,
L'équipe LocHouse
            """
        else:
            subject = 'Identité rejetée - LocHouse'
            message = f"""
Bonjour {user.get_full_name()},

Votre document d'identité a été rejeté.

Raison: {notes}

Veuillez soumettre un nouveau document.

Cordialement,
L'équipe LocHouse
            """
            logger.info(f"Identité rejetée pour l'utilisateur ID: {user_id}. Raison: {notes}")
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Email de vérification d'identité ({status}) envoyé avec succès à {user.email} (User ID: {user_id})")
        return f"Email de vérification d'identité envoyé à {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur avec l'ID {user_id} n'existe pas")
        raise
    except Exception as exc:
        logger.warning(
            f"Échec de l'envoi d'email de vérification d'identité pour l'utilisateur ID: {user_id}. "
            f"Tentative {self.request.retries + 1}/{self.max_retries}. "
            f"Erreur: {str(exc)}"
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_account_status_email_task(self, user_id, is_active, reason=''):
    """
    Tâche asynchrone pour envoyer un email de blocage/déblocage de compte
    """
    action_text = 'débloqué' if is_active else 'bloqué'
    logger.info(f"Début de l'envoi d'email de changement de statut de compte ({action_text}) pour l'utilisateur ID: {user_id}")
    
    try:
        user = User.objects.get(id=user_id)
        logger.debug(f"Utilisateur trouvé: {user.email}")
        
        subject = f'Compte {action_text} - LocHouse'
        message = f"""
Bonjour {user.get_full_name()},

Votre compte a été {action_text}.

Raison: {reason}

Cordialement,
L'équipe LocHouse
        """
        
        logger.info(f"Compte {action_text} pour l'utilisateur ID: {user_id}. Raison: {reason}")
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Email de statut de compte ({action_text}) envoyé avec succès à {user.email} (User ID: {user_id})")
        return f"Email de statut de compte envoyé à {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur avec l'ID {user_id} n'existe pas")
        raise
    except Exception as exc:
        logger.warning(
            f"Échec de l'envoi d'email de statut de compte pour l'utilisateur ID: {user_id}. "
            f"Tentative {self.request.retries + 1}/{self.max_retries}. "
            f"Erreur: {str(exc)}"
        )
        raise self.retry(exc=exc, countdown=60)