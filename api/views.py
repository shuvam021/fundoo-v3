import logging

from django.core.cache import cache
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser

from api.authentication import JWTAuthentication
from api.models import Label, Note, User
from api.serializers import LabelSerializer, NoteSerializer, UserSerializer
from api.tasks import task_send_verify_user_email, task_send_forget_password_email
from api.utils import decode_jwt_token, ReturnResponse

logger = logging.getLogger(__name__)


# Create your views here.
class AuthorisationViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    http_method_names = ['post']

    @swagger_auto_schema(request_body=UserSerializer)
    @action(detail=False, methods=['post'])
    def register(self, request):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return ReturnResponse(data=serializer.data, status_code=status.HTTP_201_CREATED)
            return ReturnResponse(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('email', openapi.TYPE_STRING, type=openapi.TYPE_STRING, required=True), ],
        responses={200: 'message sent'}, )
    @action(detail=False, methods=['post'])
    def send_verification_email(self, request):
        email = request.data.get('email')
        user = get_object_or_404(User, email=email)
        try:
            if user:
                task_send_verify_user_email.delay(user_id=user.id, email=user.email)
                return ReturnResponse(message='message sent', status_code=status.HTTP_200_OK)
            return ReturnResponse(status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('email', openapi.TYPE_STRING, type=openapi.TYPE_STRING, required=True), ],
        responses={200: 'message sent'}, )
    @action(detail=False, methods=['post'])
    def forget_password(self, request):
        try:
            user = get_object_or_404(User, email=request.data.get('email'))
            task_send_forget_password_email.delay(user.id, user.email)
            return ReturnResponse(status_code=status.HTTP_200_OK, message='message sent')
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(status_code=status.HTTP_400_BAD_REQUEST, message=str(e))

    @action(detail=False, methods=['post'], url_path='<str:token>/update_password/')
    def update_password(self, request, token=None):
        try:
            payload = decode_jwt_token(token)
            user = get_object_or_404(User, pk=payload.get('id'))
            password = request.data.get('password1')
            password2 = request.data.get('password2')
            if password != password2:
                raise ValueError('password 1 not matched with password2')
            user.set_password(password)
            user.save()
            return ReturnResponse(status_code=status.HTTP_200_OK, message='password updated')
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='(?P<token>[^/.]+)/verify_user')
    def verify_user(self, request, token=None):
        try:
            payload = decode_jwt_token(token)
            user = get_object_or_404(User, pk=payload.get('id'))
            if user:
                user.is_verified = True
                user.save()
                return ReturnResponse(status_code=status.HTTP_200_OK, message='verified')
            return ReturnResponse(status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(status_code=status.HTTP_400_BAD_REQUEST, message=str(e))


class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAdminUser,)
    serializer_class = UserSerializer
    http_method_names = ['get']
    queryset = User.objects.all()

    def list(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(self.get_queryset(), many=True)
            return ReturnResponse(data=serializer.data, status_code=200)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=400)

    def retrieve(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(self.get_queryset().get(pk=kwargs.get('pk')))
            return ReturnResponse(data=serializer.data, status_code=200)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=400)


class NoteViewSet(viewsets.ModelViewSet):
    authentication_classes = (JWTAuthentication,)
    serializer_class = NoteSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Note.objects.filter(user=user)
        return queryset

    def update_cache(self, user_id):
        """Update cached memory"""
        json_data = [{item.id: model_to_dict(item)} for item in self.get_queryset()]
        cache.set(user_id, json_data)

    def list(self, request, *args, **kwargs):
        try:
            dataset = cache.get(request.user.id)
            if dataset:
                data = [v for item in dataset for k, v in item.items()]
                return ReturnResponse(data=data)
            return ReturnResponse(message="No data found", status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            cached_data = list(cache.get(request.user.id))
            if cached_data:
                dataset = list(filter(None, [i.get(int(pk)) for i in cached_data]))
                data = {} if len(dataset) == 0 else dataset[0]
                return ReturnResponse(data=data)
            return ReturnResponse(status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            data.update({'user': request.user.id})
            serializer = self.get_serializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                self.update_cache(request.user.id)
                return ReturnResponse(data=serializer.data, status_code=status.HTTP_201_CREATED)
            return ReturnResponse(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            note = get_object_or_404(Note, pk=pk)
            serializer = self.get_serializer(note, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                self.update_cache(request.user.id)
                return ReturnResponse(data=serializer.data, status_code=status.HTTP_200_OK)
            return ReturnResponse(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            note = get_object_or_404(Note, pk=pk)
            note.delete()
            self.update_cache(request.user.id)
            return ReturnResponse(message='Delete successful', status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)


class LabelViewSet(viewsets.ModelViewSet):
    authentication_classes = (JWTAuthentication,)
    serializer_class = LabelSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Label.objects.filter(author=user)
        return queryset

    def list(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(self.get_queryset(), many=True)
            return ReturnResponse(data=serializer.data)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset().get(pk=kwargs.get('pk'))
            serializer = self.get_serializer(qs)
            return ReturnResponse(data=serializer.data)
        except Exception as e:
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            data.update({'author': request.user.id})
            serializer = self.get_serializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return ReturnResponse(data=serializer.data, status_code=status.HTTP_201_CREATED)
            return ReturnResponse(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset().get(pk=kwargs.get('pk'))
            serializer = self.get_serializer(qs, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return ReturnResponse(data=serializer.data, status_code=status.HTTP_200_OK)
            return ReturnResponse(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset().get(pk=kwargs.get('pk'))
            if qs:
                qs.delete()
                return ReturnResponse(status_code=status.HTTP_204_NO_CONTENT)
            return ReturnResponse(status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(e)
            return ReturnResponse(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)
