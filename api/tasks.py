from celery import shared_task

from api.utils import forget_password_email, verification_mail


@shared_task
def task_send_forget_password_email(user_id, email, request=None):
    forget_password_email(user_id, email, request)
    return 'send_forget_password_task'


@shared_task
def task_send_verify_user_email(user_id, email, request=None):
    verification_mail(user_id, email, request)
    return 'send_email_to_verify_user_task'
