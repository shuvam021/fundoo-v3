import logging

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, views
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.models import Label, Note, User
from api.serializers import LabelSerializer, NoteSerializer, UserSerializer
from api.tasks import task_send_verify_user_email, task_send_forget_password_email
from api.utils import decode_jwt_token

logger = logging.getLogger(__name__)


# Create your views here.
class RegisterApiView(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Exception as e:
            logger.exception(e)
            return Response(serializer.errors)


class SendVerificationApiView(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        user = get_object_or_404(User, email=email)
        try:
            if user:
                task_send_verify_user_email.delay(user_id=user.id, email=user.email)
                return Response(status=200)
        except Exception as e:
            logger.exception(e)
            return Response(status=400)


class UserVerificationApiView(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request, **kwargs):
        try:
            payload = decode_jwt_token(kwargs.get('token'))
            user = get_object_or_404(User, pk=payload.get('id'))
            if user:
                user.is_verified = True
                user.save()
            return Response(status=200)
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)})


class ForgetPasswordApiView(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            user = get_object_or_404(User, email=request.data.get('email'))
            task_send_forget_password_email.delay(user.id, user.email)
            return Response(status=200)
        except Exception as e:
            logger.exception(e)
            return Response(status=400)


class UpdatePasswordApiView(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request, token=None):
        try:
            payload = decode_jwt_token(token)
            user = get_object_or_404(User, pk=payload.get('id'))

            password = request.data.get('password1')
            password2 = request.data.get('password2')
            if password != password2:
                raise ValueError('password 1 not matched with password2')

            user.set_password(password)
            user.save()
            return Response(status=200)
        except Exception as e:
            logger.exception(e)
            return Response(status=400)


class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAdminUser,)
    serializer_class = UserSerializer
    http_method_names = ['get']
    queryset = User.objects.all()


class NoteViewSet(viewsets.ModelViewSet):
    authentication_classes = (JWTAuthentication,)
    serializer_class = NoteSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Note.objects.filter(user=user)
        return queryset


class LabelViewSet(viewsets.ModelViewSet):
    authentication_classes = (JWTAuthentication,)
    serializer_class = LabelSerializer
    queryset = Label.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = Label.objects.filter(author=user)
        return queryset
