# 다음 작업 체크리스트 (Next Steps)

이 파일은 다음 작업을 시작할 때 참고하세요.

---

## 🚀 빠른 시작 가이드

### 1. 환경 설정 (5분)

```bash
# Docker 서비스 실행
docker-compose up -d

# 서비스 상태 확인 (모두 healthy/running이어야 함)
docker-compose ps

# 테스트 실행 (30개 테스트, 모두 통과해야 함)
docker-compose exec web python manage.py test products.tests --verbosity=1
```

**예상 결과**:
```
Ran 30 tests in 1.4s
OK ✅
```

### 2. 현재 코드 상태 확인 (2분)

```bash
# Git 상태 확인
git status

# 최근 커밋 확인
git log --oneline -5
```

### 3. 문서 읽기 (10분)

| 문서 | 용도 | 읽기 시간 |
|------|------|---------|
| **PROGRESS.md** | 현재까지의 작업 진행사항 | 10분 |
| **TESTING.md** | 테스트 실행 방법 | 5분 |
| **ERROR_HANDLING.md** | 에러 처리 전략 | 5분 |
| **.claude/CLAUDE.md** | 프로젝트 아키텍처 | 5분 |

---

## 📋 3단계: 타입 힌팅 추가

### 예상 시간: 1시간
### 예상 난이도: ⭐ (낮음)

### 할 일

#### 1. products/views.py (30분)
```python
# 현재 상태
def search(self, request):
    query = request.query_params.get('q', '')

# 개선할 상태
from typing import Dict, Any
from rest_framework.request import Request
from rest_framework.response import Response

def search(self, request: Request) -> Response:
    query: str = request.query_params.get('q', '')
    # ...

def _add_ranking(self, keyword: str) -> None:
    # ...
```

**변경할 메소드**:
- `search()` → `search(self, request: Request) -> Response`
- `ranking()` → `ranking(self, request: Request) -> Response`
- `_add_ranking()` → `_add_ranking(self, keyword: str) -> None`

#### 2. products/serializers.py (15분)
```python
# Serializer 메소드에 타입 힌팅 추가
from typing import Dict, Any, List
from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    def to_representation(self, instance: Any) -> Dict[str, Any]:
        # ...
```

#### 3. products/models.py (15분)
```python
# 모델 메소드에 타입 힌팅 추가
from typing import str

class Brand(TimeStampedModel):
    def __str__(self) -> str:
        return self.name
```

### 테스트 실행
```bash
docker-compose exec web python manage.py test products.tests --verbosity=1

# mypy를 사용한 타입 검사 (설치 필요)
pip install mypy
mypy products/
```

### 커밋 메시지 템플릿
```
타입 힌팅 추가 (3단계 완료)

- products/views.py: 모든 메소드에 타입 힌팅 추가
- products/serializers.py: Serializer 메소드에 타입 힌팅 추가
- products/models.py: 모델 메소드에 타입 힌팅 추가

포트폴리오 임팩트: ⭐⭐⭐ 중간
```

---

## 📋 4단계: 페이지네이션 추가

### 예상 시간: 1시간
### 예상 난이도: ⭐⭐ (중간)

### 할 일

#### 1. settings.py 설정 (10분)
```python
# REST Framework 페이지네이션 설정
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

#### 2. views.py 수정 (20분)
```python
@action(detail=False, methods=['get'])
def search(self, request):
    # 검색 결과 가져오기
    products = Product.objects.filter(id__in=product_ids)

    # 페이지네이션 적용
    page = self.paginate_queryset(products)
    if page is not None:
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    serializer = self.get_serializer(products, many=True)
    return Response(serializer.data)
```

#### 3. 테스트 추가 (20분)
```python
class ProductSearchPaginationTests(TestCase):
    def test_search_pagination_first_page(self):
        # /api/products/items/search/?q=test&page=1
        pass

    def test_search_pagination_page_size(self):
        # page_size 파라미터 테스트
        pass

    def test_search_pagination_invalid_page(self):
        # 잘못된 페이지 번호 테스트
        pass
```

#### 4. Swagger 문서 (10분)
```python
@swagger_auto_schema(
    manual_parameters=[
        openapi.Parameter('q', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    ]
)
```

### 테스트 실행
```bash
docker-compose exec web python manage.py test products.tests --verbosity=1
```

### 예상 결과
```
# 페이지네이션 응답 예시
{
    "count": 100,
    "next": "http://api.example.com/api/products/items/search/?q=test&page=2",
    "previous": null,
    "results": [...]
}
```

### 커밋 메시지 템플릿
```
페이지네이션 추가 (4단계 완료)

- REST Framework 페이지네이션 설정
- 검색 API에 페이지네이션 적용
- 페이지네이션 테스트 추가 (3개)
- Swagger 문서에 page, page_size 파라미터 추가

포트폴리오 임팩트: ⭐⭐⭐⭐ 높음
```

---

## 📋 5단계: 성능 최적화

### 예상 시간: 2시간
### 예상 난이도: ⭐⭐⭐ (어려움)

### 할 일

#### 1. Elasticsearch 결과 순서 보존 (30분)
```python
# 현재 문제: Elasticsearch 결과 순서가 DB 쿼리 후 순서와 다름
product_ids = [hit.meta.id for hit in response]  # [2, 5, 1]
products = Product.objects.filter(id__in=product_ids)  # [1, 2, 5] (순서 다름)

# 개선: 순서 보존
from django.db.models import Case, When, Value, IntegerField

preserved_order = Case(
    *[When(pk=pk, then=Value(i)) for i, pk in enumerate(product_ids)],
    output_field=IntegerField()
)
products = Product.objects.filter(id__in=product_ids).order_by(preserved_order)
```

#### 2. 캐싱 전략 최적화 (30분)
```python
# 검색 결과 캐싱 시간 조정
# 현재: 1시간 (3600초)
# 개선: 인기도에 따라 다르게 캐싱
#      - 인기 검색어: 2시간 (7200초)
#      - 일반 검색어: 1시간 (3600초)
#      - 낮은 인기: 30분 (1800초)

cache_ttl = 7200 if ranking_score > 10 else (1800 if ranking_score < 2 else 3600)
cache.set(cache_key, data, timeout=cache_ttl)
```

#### 3. DB 쿼리 최적화 (20분)
```python
# 현재 상태
products = Product.objects.filter(id__in=product_ids)

# 개선: select_related, prefetch_related 최적화
products = Product.objects.filter(id__in=product_ids) \
    .select_related('brand') \
    .prefetch_related('ingredients') \
    .only('id', 'name', 'price', 'image_url', 'brand__name')
```

#### 4. 성능 테스트 추가 (30분)
```python
class ProductSearchPerformanceTests(TransactionTestCase):
    def test_search_response_time_cached(self):
        # 캐시된 검색: 1ms 이내
        pass

    def test_search_response_time_uncached(self):
        # 캐시 미스 검색: 200ms 이내
        pass

    def test_large_dataset_search(self):
        # 대량 데이터(10,000개) 검색 성능
        pass

    def test_concurrent_searches(self):
        # 동시 요청 처리 성능
        pass
```

#### 5. 문서 업데이트 (10분)
```bash
# PERFORMANCE.md 작성
# - 성능 메트릭 (응답 시간, 메모리 사용량)
# - 최적화 전후 비교
# - 병목 분석
```

### 성능 측정 방법
```bash
# Django debug toolbar 설치 (개발 환경)
pip install django-debug-toolbar

# 요청 시간 측정
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/products/items/search/?q=test"

# Redis 성능 확인
docker-compose exec redis redis-cli INFO stats
```

### 커밋 메시지 템플릿
```
성능 최적화 (5단계 완료)

- Elasticsearch 결과 순서 보존 구현
- 캐싱 전략 인기도 기반 최적화
- DB 쿼리 최적화 (select_related, prefetch_related)
- 성능 테스트 추가 (4개)
- 성능 메트릭 문서화

포트폴리오 임팩트: ⭐⭐⭐⭐⭐ 매우 높음

성능 개선:
- 캐시 히트: 1ms (변화 없음)
- 캐시 미스: 150ms → 100ms (33% 개선)
- DB 쿼리: 50ms → 20ms (60% 개선)
```

---

## 📋 선택 과제: 추가 개선 아이디어

### A. API 인증 추가 (JWT)
**난이도**: ⭐⭐⭐ | **시간**: 2시간 | **임팩트**: ⭐⭐⭐⭐

### B. 검색 필터 추가 (가격, EWG 점수)
**난이도**: ⭐⭐ | **시간**: 1.5시간 | **임팩트**: ⭐⭐⭐

### C. 실시간 알림 (Websocket)
**난이도**: ⭐⭐⭐⭐ | **시간**: 3시간 | **임팩트**: ⭐⭐⭐

### D. 분석 대시보드 (사용자 행동 분석)
**난이도**: ⭐⭐⭐ | **시간**: 2시간 | **임팩트**: ⭐⭐⭐⭐

### E. CI/CD 파이프라인 (GitHub Actions)
**난이도**: ⭐⭐ | **시간**: 1.5시간 | **임팩트**: ⭐⭐⭐⭐

---

## 📱 유용한 명령어 (Quick Reference)

### Docker
```bash
# 전체 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f web

# 서비스 재시작
docker-compose restart web

# 컨테이너 접속
docker-compose exec web bash
```

### Django 테스트
```bash
# 모든 테스트 실행
docker-compose exec web python manage.py test products.tests

# 특정 테스트만 실행
docker-compose exec web python manage.py test products.tests.ProductSearchAPITests

# 코드 커버리지 확인
docker-compose exec web coverage run --source='products' manage.py test products.tests
docker-compose exec web coverage report
```

### Git
```bash
# 현재 변경사항 확인
git status

# 파일 스테이징
git add -A

# 커밋
git commit -m "your message"

# 로그 확인
git log --oneline -10
```

### Django Shell
```bash
# Django 쉘 실행
docker-compose exec web python manage.py shell

# 쉘에서 테스트
>>> from products.models import Brand, Product
>>> Brand.objects.count()
>>> Product.objects.all()[:5]
```

---

## ✅ 완료 체크리스트 (작업 전 확인)

### 시작하기 전
- [ ] Docker 서비스 모두 실행 확인 (`docker-compose ps`)
- [ ] 테스트 30개 모두 통과 확인
- [ ] Git 상태 깨끗함 (`git status` 결과 nothing to commit)
- [ ] 문서 읽음 (PROGRESS.md, TESTING.md)

### 작업 중
- [ ] 한 번에 한 가지 단계만 진행
- [ ] 각 변경 후 테스트 실행
- [ ] 자주 커밋 (작은 단위로)
- [ ] 의존하는 라이브러리 설치 필요하면 requirements.txt 업데이트

### 작업 완료 후
- [ ] 모든 테스트 통과 확인
- [ ] 새로운 테스트 추가했으면 테스트도 함께 커밋
- [ ] 문서 업데이트 (필요하면)
- [ ] 커밋 메시지 명확하게 작성

---

## 🆘 문제 해결

### 테스트 실패
```bash
# 1. 전체 테스트 실행해서 어떤 테스트가 실패하는지 확인
docker-compose exec web python manage.py test products.tests -v 2

# 2. 특정 테스트 실행해서 상세 메시지 확인
docker-compose exec web python manage.py test products.tests.ProductSearchAPITests.test_search_caching_hit -v 2

# 3. 로그 확인
docker-compose logs web
```

### 서비스 연결 불가
```bash
# 1. 서비스 상태 확인
docker-compose ps

# 2. 서비스 재시작
docker-compose restart

# 3. 로그 확인
docker-compose logs elasticsearch
docker-compose logs redis
docker-compose logs db
```

### Git 커밋 실패
```bash
# 변경사항 확인
git diff

# 강제 추가 (필요한 경우)
git add -A --force

# 커밋 재시도
git commit -m "message"
```

---

## 📞 참고 자료

- **프로젝트 README**: `/README.md`
- **테스트 가이드**: `/TESTING.md`
- **에러 처리**: `/ERROR_HANDLING.md`
- **프로젝트 구조**: `/.claude/CLAUDE.md`
- **진행사항**: `/PROGRESS.md`

---

**마지막 업데이트**: 2026-01-25
**상태**: 2단계 완료, 3-5단계 대기 중
