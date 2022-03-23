from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.reverse import reverse_lazy


def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.exceptions.ExpiredSignatureError as e:
        raise e


def generate_jwt_token(user_id):
    token = jwt.encode(
        {
            "id": user_id,
            'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=3600)
        },
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    return str(token)


def forget_password_email(user_id, email, request=None):
    token = generate_jwt_token(user_id)
    endpoint = reverse_lazy('update-password', kwargs={'token': token}, requests=request)
    subject = "Change your password"
    body = f"Hii, {email}\n"
    body += f"use this link to change your password\n{endpoint}"
    return send_mail(subject, body, settings.EMAIL_HOST_USER, [email], fail_silently=False)


def verification_mail(user_id, email, request=None):
    token = generate_jwt_token(user_id)
    endpoint = reverse_lazy('user-verify', kwargs={'token': token}, requests=request)
    subject = "New user Verification Notifier"
    body = f"Try this link to verify your account\n{endpoint}"
    body += f"http://127.0.0.1:8000/api/verify_user/{token}/"
    return send_mail(subject, body, settings.EMAIL_HOST_USER, [email], fail_silently=False)
