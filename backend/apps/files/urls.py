from rest_framework.routers import DefaultRouter

from .views import FileViewSet, FolderViewSet

app_name = "files"

router = DefaultRouter()
router.register("folders", FolderViewSet, basename="folder")
router.register("files", FileViewSet, basename="file")

urlpatterns = router.urls
