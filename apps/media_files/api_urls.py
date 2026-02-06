from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'media_files', views.MediaFileViewSet, basename='media_files')

urlpatterns = router.urls
