from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache             # Django 캐시 모듈
from django_redis import get_redis_connection   # Redis 직접 제어 (랭킹용)
from elasticsearch_dsl import Q

from .models import Product
from .serializers import ProductSerializer
from .documents import ProductDocument

# --- Swagger용 임포트 추가 ---
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ProductViewSet(viewsets.ModelViewSet):
    """
    상품 조회, 생성, 수정, 삭제 API
    """
    queryset = Product.objects.all().select_related('brand').prefetch_related('ingredients')
    serializer_class = ProductSerializer

    # 핵심: /api/products/items/search/?q=검색어
    # [1] 검색 API 꾸미기
    @swagger_auto_schema(
        operation_summary="통합 상품 검색 (MySQL + ES)",
        operation_description="상품명, 브랜드명, 성분명을 통합 검색합니다. (Redis 캐싱 적용)",
        manual_parameters=[
            openapi.Parameter(
                'q',
                openapi.IN_QUERY,
                description='검색어 (예: 토너, 이니스프리)',
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')

        if not query:
            return Response({'error': '검색어를 입력해주세요.'}, status=400)

        # [Step 1] Redis 캐시 확인 (Key: search:검색어)
        cache_key = f"search:{query}"
        cached_result = cache.get(cache_key)

        if cached_result:
            print(f"⚡ Cache Hit! (Redis에서 가져옴): {query}")
            # 캐시가 있어도 랭킹 점수는 올려야 함!
            self._add_ranking(query)
            return Response(cached_result)

        # [Step 2] 캐시 없으면 Elasticsearch 검색
        print(f"🐢 Cache Miss... (ES 검색 수행): {query}")

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

        # [Step 3] DB에서 상세 정보 조회
        # 결과 변환 (ES 데이터를 바로 줄 수도 있지만, 일관성을 위해 Serializer 태움)
        # *주의: 실무에선 DB 다시 조회 안 하고 ES 결과(_source)를 바로 줍니다. (속도 위해)
        # 여기선 간단하게 ID로 DB 다시 조회하는 방식으로 구현합니다.
        product_ids = [hit.meta.id for hit in response]

        # MySQL에서 순서대로 가져오기 (preserve_order)
        products = Product.objects.filter(id__in=product_ids)
        serializer = self.get_serializer(products, many=True)
        data = serializer.data

        # [Step 4] 결과 Redis에 저장 (유효시간 1시간 = 3600초)
        cache.set(cache_key, data, timeout=60*60)

        # [Step 5] 랭킹 집계
        self._add_ranking(query)

        return Response(serializer.data)

    # 2. 랭킹 집계 함수 (내부 호출용)
    def _add_ranking(self, keyword):
        con = get_redis_connection("default")
        # Sorted Set(ZSET) 자료구조 사용: 점수 1점 증가 (ZINCRBY)
        con.zincrby("search_ranking", 1, keyword)

    # 3. 실시간 검색어 순위 조회 API
    # [2] 랭킹 API 꾸미기
    @swagger_auto_schema(
        operation_summary="실시간 인기 검색어 순위",
        operation_description="Redis에 집계된 실시간 검색어 Top 10을 반환합니다."
    )
    @action(detail=False, methods=['get'])
    def ranking(self, request):
        con = get_redis_connection("default")
        # 점수 높은 순으로 상위 10개 가져오기 (ZREVRANGE 0 -1)
        # withscores=True: 점수도 같이 반환
        ranks = con.zrevrange("search_ranking", 0, 9, withscores=True)

        # 보기 좋게 JSON 변환
        result = [
            {"rank": i+1, "keyword": keyword.decode('utf-8'), "score": int(score)}
            for i, (keyword, score) in enumerate(ranks)
        ]
        return Response(result)