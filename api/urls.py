from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()

router.register('auth', viewset=views.AuthorisationViewSet, basename='auth')
router.register('label', viewset=views.LabelViewSet, basename='labels')
router.register('note', viewset=views.NoteViewSet, basename='notes')
router.register('user', viewset=views.UserViewSet, basename='users')

urlpatterns = router.urls
