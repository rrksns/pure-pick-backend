from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register(r'items', ProductViewSet) # /api/products/items/ 주소 생성

urlpatterns = [
    path('', include(router.urls)),
]