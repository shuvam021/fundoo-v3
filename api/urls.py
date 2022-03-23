from rest_framework.routers import DefaultRouter

from api import views

app_name = 'api'

router = DefaultRouter()

router.register('user', viewset=views.UserViewSet, basename='users')
router.register('note', viewset=views.NoteViewSet, basename='notes')
router.register('label', viewset=views.LabelViewSet, basename='labels')

urlpatterns = router.urls
