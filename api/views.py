import logging

from django.core.cache import cache
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from api.authentication import JWTAuthentication
from api.models import Label, Note, User
from api.serializers import LabelSerializer, NoteSerializer, UserSerializer
from api.tasks import task_send_verify_user_email, task_send_forget_password_email
from api.utils import decode_jwt_token

logger = logging.getLogger(__name__)


# Create your views here.
class AuthorisationViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    http_method_names = ['post']

    @swagger_auto_schema(request_body=UserSerializer)
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Exception as e:
            logger.exception(e)
            return Response(serializer.errors)

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
                return Response(data={200: 'message sent'}, status=200)
            return Response(status=404)
        except Exception as e:
            logger.exception(e)
            return Response(status=400)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('email', openapi.TYPE_STRING, type=openapi.TYPE_STRING, required=True), ],
        responses={200: 'message sent'}, )
    @action(detail=False, methods=['post'])
    def forget_password(self, request):
        try:
            user = get_object_or_404(User, email=request.data.get('email'))
            task_send_forget_password_email.delay(user.id, user.email)
            return Response(status=200, data={'message': 'message sent'})
        except Exception as e:
            logger.exception(e)
            return Response(status=400)

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
            return Response(status=200, data={"message": 'password changed'})
        except Exception as e:
            logger.exception(e)
            return Response(status=400)

    @action(detail=False, methods=['post'], url_path='(?P<token>[^/.]+)/verify_user')
    def verify_user(self, request, token=None):
        try:
            payload = decode_jwt_token(token)
            user = get_object_or_404(User, pk=payload.get('id'))
            if user:
                user.is_verified = True
                user.save()
                return Response(status=200)
            return Response(status=404)
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

    def update_cache(self, user_id):
        """Update cached memory"""
        json_data = [{item.id: model_to_dict(item)} for item in self.get_queryset()]
        cache.set(user_id, json_data)

    def list(self, request, *args, **kwargs):
        try:
            dataset = cache.get(request.user.id)
            if dataset:
                data = [v for item in dataset for k, v in item.items()]
                return Response(data=data)
            return Response(data=[])
        except Exception as e:
            logger.exception(e)
            return Response(status=400)

    def retrieve(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            cached_data = list(cache.get(request.user.id))
            if cached_data:
                dataset = list(filter(None, [i.get(int(pk)) for i in cached_data]))
                data = {} if len(dataset) == 0 else dataset[0]
                return Response(data=data, status=200)
            return Response(data={})
        except Exception as e:
            logger.exception(e)
            return Response(status=400)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data.update({'user': request.user.id})
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            self.update_cache(request.user.id)
            return Response(data=serializer.data)
        except Exception as e:
            logger.exception(e)
            return Response(data=serializer.errors)

    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        note = get_object_or_404(Note, pk=pk)
        serializer = self.get_serializer(note, data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            self.update_cache(request.user.id)
            return Response(data=serializer.data)
        except Exception as e:
            logger.exception(e)
            return Response(data=serializer.errors)

    def destroy(self, request, *args, **kwargs):
        try:
            pk = kwargs.get('pk')
            note = get_object_or_404(Note, pk=pk)
            note.delete()
            self.update_cache(request.user.id)
            return Response(status=204)
        except Exception as e:
            logger.exception(e)
            return Response({'message': str(e)})


class LabelViewSet(viewsets.ModelViewSet):
    authentication_classes = (JWTAuthentication,)
    serializer_class = LabelSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Label.objects.filter(author=user)
        return queryset
