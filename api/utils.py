from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response


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


def ReturnResponse(message="", data=None, status_code=status.HTTP_200_OK):
    if not data:
        data = {}
    return Response(
        {'status': status_code, 'message': message, 'data': data},
        status_code
    )
