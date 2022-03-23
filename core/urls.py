from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from api.views import (RegisterApiView, UserVerificationApiView, SendVerificationApiView, ForgetPasswordApiView,
                       UpdatePasswordApiView)

schema_view = get_schema_view(public=True, permission_classes=(AllowAny,))

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('api-auth/', include('rest_framework.urls')), path('admin/', admin.site.urls),
    path('api/register', RegisterApiView.as_view(), name='register'),

    path('api/send-verification', SendVerificationApiView.as_view(), name='send-verification'),
    path('api/verify_user/<str:token>', UserVerificationApiView.as_view(), name='user-verify'),

    path('api/forget_password', ForgetPasswordApiView.as_view(), name='forget-password'),
    path('api/update_password/<str:token>', UpdatePasswordApiView.as_view(), name='update-password'),

    path('api/token/', TokenObtainPairView.as_view(), name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token-verify'),

    path('api/', include('api.urls', namespace='api')),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
