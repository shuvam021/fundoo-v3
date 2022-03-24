from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings


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
