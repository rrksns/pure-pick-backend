from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from .documents import ProductDocument
from elasticsearch_dsl import Q

class ProductViewSet(viewsets.ModelViewSet):
    """
    상품 조회, 생성, 수정, 삭제 API
    """
    queryset = Product.objects.all().select_related('brand').prefetch_related('ingredients')
    serializer_class = ProductSerializer

    # 핵심: /api/products/items/search/?q=검색어
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')

        if not query:
            return Response({'error': '검색어를 입력해주세요.'}, status=400)

        # Elasticsearch Query (DSL)
        # 상품명(name), 브랜드명(brand.name), 성분명(ingredients.name)에서 다 찾음!
        # fuzzy: 오타가 있어도 찾아줌 (ex: '토너' -> '투너')
        q = Q('multi_match',
              query=query,
              fields=['name', 'brand.name', 'ingredients.name'],
              fuzziness='AUTO')

        # 검색 실행
        search_result = ProductDocument.search().query(q)
        response = search_result.execute()

        # 결과 변환 (ES 데이터를 바로 줄 수도 있지만, 일관성을 위해 Serializer 태움)
        # *주의: 실무에선 DB 다시 조회 안 하고 ES 결과(_source)를 바로 줍니다. (속도 위해)
        # 여기선 간단하게 ID로 DB 다시 조회하는 방식으로 구현합니다.
        product_ids = [hit.meta.id for hit in response]

        # MySQL에서 순서대로 가져오기 (preserve_order)
        products = Product.objects.filter(id__in=product_ids)
        serializer = self.get_serializer(products, many=True)

        return Response(serializer.data)