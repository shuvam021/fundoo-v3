from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views

schema_view = get_schema_view(public=True, permission_classes=(AllowAny,))

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('api-auth/', include('rest_framework.urls')), path('admin/', admin.site.urls),
    path('api/login/', TokenObtainPairView.as_view(), name='login'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name='login-refresh'),
    path('api/login/verify/', TokenVerifyView.as_view(), name='login-verify'),

    path('api/', include('api.urls'), name='api'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # front-end
    path('register/', views.RegistrationView.as_view(), name='temp-reg'),
    path('login/', views.LoginView.as_view(), name='temp-login'),
    path('logout/', views.logout_view, name='temp-logout'),
]
