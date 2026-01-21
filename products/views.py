from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    """
    상품 조회, 생성, 수정, 삭제 API
    """
    queryset = Product.objects.all().select_related('brand').prefetch_related('ingredients')
    serializer_class = ProductSerializer