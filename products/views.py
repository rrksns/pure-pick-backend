import logging
from typing import Dict, List, Any, Optional
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from django.core.cache import cache             # Django 캐시 모듈
from django_redis import get_redis_connection   # Redis 직접 제어 (랭킹용)
from elasticsearch_dsl import Q
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from redis.exceptions import ConnectionError as RedisConnectionError

from .models import Product
from .serializers import ProductSerializer
from .documents import ProductDocument

# --- Swagger용 임포트 추가 ---
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# 로깅 설정
logger = logging.getLogger(__name__)

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
        operation_description="상품명, 브랜드명, 성분명을 통합 검색합니다. (Redis 캐싱 적용, 페이지네이션 지원)",
        manual_parameters=[
            openapi.Parameter(
                'q',
                openapi.IN_QUERY,
                description='검색어 (예: 토너, 이니스프리)',
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description='페이지 번호 (기본값: 1)',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description='페이지당 결과 수 (기본값: 20)',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request: Request) -> Response:
        """
        상품 검색 API

        쿼리 파라미터:
        - q: 검색어 (필수, 최소 1자, 최대 100자)

        반환:
        - 검색 결과 상품 리스트 (배열)
        - 캐시 히트 시 빠른 응답, 미스 시 Elasticsearch에서 검색

        에러 코드:
        - 400: 검색어 미입력 또는 유효하지 않음
        - 503: Elasticsearch 또는 Redis 연결 불가
        - 500: 예상치 못한 서버 오류
        """
        try:
            # [Step 0] 입력값 검증
            query = request.query_params.get('q', '').strip()

            # 검색어 유효성 검사
            if not query:
                logger.warning("검색 요청: 빈 검색어")
                return Response(
                    {'error': '검색어를 입력해주세요.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if len(query) > 100:
                logger.warning(f"검색 요청: 검색어 길이 초과 ({len(query)}자)")
                return Response(
                    {'error': '검색어는 100자 이하여야 합니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # [Step 1] Redis 캐시 확인 (Key: search:검색어)
            cache_key = f"search:{query}"

            try:
                cached_result = cache.get(cache_key)
                if cached_result:
                    logger.info(f"캐시 히트: {query}")
                    # 캐시가 있어도 랭킹 점수는 올려야 함!
                    self._add_ranking(query)
                    return Response(cached_result)
            except Exception as e:
                logger.warning(f"캐시 조회 실패: {str(e)}")
                # 캐시 실패해도 계속 진행

            # [Step 2] 캐시 없으면 Elasticsearch 검색
            logger.info(f"캐시 미스, Elasticsearch 검색 시작: {query}")

            try:
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

            except ESConnectionError as e:
                logger.error(f"Elasticsearch 연결 실패: {e.__class__.__name__}")
                return Response(
                    {
                        'error': 'Elasticsearch 서비스에 연결할 수 없습니다.',
                        'detail': '검색 기능을 일시적으로 사용할 수 없습니다.'
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except Exception as e:
                logger.error(f"Elasticsearch 검색 오류: {e.__class__.__name__}: {str(e)}")
                return Response(
                    {
                        'error': '검색 중 오류가 발생했습니다.',
                        'detail': str(e)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # [Step 3] DB에서 상세 정보 조회
            try:
                product_ids = [hit.meta.id for hit in response]

                if not product_ids:
                    # 결과가 없어도 에러가 아님
                    logger.info(f"검색 결과 없음: {query}")
                    empty_response = {
                        'count': 0,
                        'next': None,
                        'previous': None,
                        'results': []
                    }
                    try:
                        cache.set(cache_key, empty_response, timeout=60*60)
                    except Exception as e:
                        logger.warning(f"빈 결과 캐싱 실패: {str(e)}")
                    return Response(empty_response)

                # MySQL에서 순서대로 가져오기
                products = Product.objects.filter(id__in=product_ids)

                # 페이지네이션 적용
                page = self.paginate_queryset(products)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    data = self.get_paginated_response(serializer.data).data
                else:
                    serializer = self.get_serializer(products, many=True)
                    data = serializer.data

            except Exception as e:
                logger.error(f"데이터베이스 조회 오류: {str(e)}")
                return Response(
                    {
                        'error': '데이터를 조회할 수 없습니다.',
                        'detail': str(e)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # [Step 4] 결과 Redis에 저장 (유효시간 1시간 = 3600초)
            try:
                cache.set(cache_key, data, timeout=60*60)
                logger.debug(f"검색 결과 캐싱 완료: {query}")
            except Exception as e:
                logger.warning(f"검색 결과 캐싱 실패 (계속 진행): {str(e)}")

            # [Step 5] 랭킹 집계
            self._add_ranking(query)

            return Response(data)

        except Exception as e:
            logger.exception(f"검색 API 예상치 못한 오류: {str(e)}")
            return Response(
                {
                    'error': '예상치 못한 오류가 발생했습니다.',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _add_ranking(self, keyword: str) -> None:
        """
        검색어 랭킹 점수 증가

        Args:
            keyword: 증가시킬 검색어

        Note:
            Redis 연결 실패 시 로그만 기록하고 계속 진행
            (랭킹은 부가 기능이므로 실패해도 검색은 진행)
        """
        try:
            con = get_redis_connection("default")
            # Sorted Set(ZSET) 자료구조 사용: 점수 1점 증가 (ZINCRBY)
            con.zincrby("search_ranking", 1, keyword)
            logger.debug(f"랭킹 업데이트: {keyword}")
        except RedisConnectionError as e:
            logger.error(f"Redis 연결 실패 (랭킹 업데이트 스킵): {str(e)}")
        except Exception as e:
            logger.error(f"랭킹 업데이트 오류: {str(e)}")

    @swagger_auto_schema(
        operation_summary="실시간 인기 검색어 순위",
        operation_description="Redis에 집계된 실시간 검색어 Top 10을 반환합니다."
    )
    @action(detail=False, methods=['get'])
    def ranking(self, request: Request) -> Response:
        """
        실시간 인기 검색어 순위 조회

        반환:
        - 상위 10개의 인기 검색어 (rank, keyword, score)
        - 점수 높은 순으로 정렬

        에러 코드:
        - 503: Redis 연결 불가
        - 500: 예상치 못한 서버 오류
        """
        try:
            con = get_redis_connection("default")
            # 점수 높은 순으로 상위 10개 가져오기 (ZREVRANGE 0 -1)
            # withscores=True: 점수도 같이 반환
            ranks = con.zrevrange("search_ranking", 0, 9, withscores=True)

            # 보기 좋게 JSON 변환
            result = [
                {"rank": i+1, "keyword": keyword.decode('utf-8'), "score": int(score)}
                for i, (keyword, score) in enumerate(ranks)
            ]

            logger.info(f"랭킹 조회 완료 (결과 수: {len(result)})")
            return Response(result)

        except RedisConnectionError as e:
            logger.error(f"Redis 연결 실패 (랭킹 조회): {str(e)}")
            return Response(
                {
                    'error': 'Redis 서비스에 연결할 수 없습니다.',
                    'detail': '인기 검색어 기능을 일시적으로 사용할 수 없습니다.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"랭킹 조회 오류: {str(e)}")
            return Response(
                {
                    'error': '인기 검색어를 조회할 수 없습니다.',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )