import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from api.models import User


class JWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth_data = get_authorization_header(request)
        if not auth_data:
            return None
        prefix, token = auth_data.decode('utf-8').split(' ')
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
        try:
            user = User.objects.get(pk=payload['user_id'])
            return (user, token)
        except jwt.DecodeError:
            raise AuthenticationFailed('Your token is invalid,login')
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Your token is expired,login')
