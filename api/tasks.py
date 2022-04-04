from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


from api.utils import generate_jwt_token


@shared_task
def task_send_forget_password_email(user_id, email):
    endpoint = f"{settings.SITE_URI}/api/auth/{generate_jwt_token(user_id)}/update_password/"
    subject = "Change your password"
    body = f"Hii, {email}\n"
    body += f"use this link to change your password\n{endpoint}"
    send_mail(subject, body, settings.EMAIL_HOST_USER, [email], fail_silently=False)
    return 'send_forget_password_task'


@shared_task
def task_send_verify_user_email(user_id, email):
    endpoint = f"{settings.SITE_URI}/api/auth/{generate_jwt_token(user_id)}/verify_user/"
    subject = "New user Verification Notifier"
    body = f"Try this link to verify your account\n{endpoint}/"
    send_mail(subject, body, settings.EMAIL_HOST_USER, [email], fail_silently=False)
    return 'send_email_to_verify_user_task'
