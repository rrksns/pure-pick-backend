# Testing Guide

이 문서는 pure-pick-backend 프로젝트의 테스트 실행 방법을 설명합니다.

## 테스트 구조

### 1. ProductModelTests
- 상품, 브랜드, 성분 모델의 기본 동작 확인
- 관계(Relationship) 테스트
- 데이터 유효성 검증

### 2. ProductSearchAPITests
- 검색 API의 기본 동작 확인
- 캐시 히트/미스 동작 검증
- 랭킹 점수 증가 확인
- Elasticsearch 쿼리 모킹

### 3. ProductRankingAPITests
- 인기 검색어 랭킹 조회 테스트
- 상위 10개 제한 검증
- 응답 형식 확인

### 4. ProductListAPITests
- 상품 목록 조회
- 상품 생성/수정/삭제 API

## 실행 방법

### Docker 환경에서 실행 (권장)

#### 모든 테스트 실행
```bash
docker-compose exec web python manage.py test products.tests --verbosity=2
```

#### 특정 테스트 클래스만 실행
```bash
# 모델 테스트만
docker-compose exec web python manage.py test products.tests.ProductModelTests --verbosity=2

# 검색 API 테스트만
docker-compose exec web python manage.py test products.tests.ProductSearchAPITests --verbosity=2

# 랭킹 API 테스트만
docker-compose exec web python manage.py test products.tests.ProductRankingAPITests --verbosity=2

# 상품 목록 API 테스트만
docker-compose exec web python manage.py test products.tests.ProductListAPITests --verbosity=2
```

#### 특정 테스트 메소드만 실행
```bash
docker-compose exec web python manage.py test products.tests.ProductModelTests.test_create_product --verbosity=2
```

### 로컬 환경에서 실행 (개발 중)

#### 전제 조건
```bash
# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt
```

#### 테스트 실행 (Elasticsearch/Redis 없이)
```bash
python manage.py test products.tests --verbosity=2
```

참고: 로컬 테스트는 Elasticsearch 연결을 시도하지 않으므로 서비스가 없어도 테스트 가능합니다.

## 테스트 커버리지 확인

### Coverage 설치 및 실행
```bash
# Docker에서
docker-compose exec web pip install coverage

# 커버리지와 함께 테스트 실행
docker-compose exec web coverage run --source='products' manage.py test products.tests

# 커버리지 리포트 생성
docker-compose exec web coverage report

# HTML 리포트 생성 (상세 분석)
docker-compose exec web coverage html
```

## 테스트 내용 상세

### ProductModelTests
| 테스트 | 목적 |
|--------|------|
| test_create_product | 상품 생성 가능 여부 확인 |
| test_product_brand_relationship | Brand와 Product의 1:N 관계 동작 |
| test_product_ingredients_relationship | Product와 Ingredient의 N:M 관계 동작 |
| test_ingredient_ewg_score_validation | EWG 점수 범위 유효성 (1-10) |
| test_product_string_representation | Product의 __str__ 메소드 |
| test_brand_string_representation | Brand의 __str__ 메소드 |

### ProductSearchAPITests (복잡 시나리오)
| 테스트 | 목적 |
|--------|------|
| test_search_empty_query | 빈 검색어 400 에러 반환 |
| test_search_no_query_param | 쿼리 파라미터 없으면 400 에러 |
| test_search_with_valid_query | 유효한 검색어 처리 |
| test_search_caching_hit | Redis 캐시 히트 확인 |
| test_search_ranking_increments | 검색 시마다 랭킹 +1 증가 |
| test_search_multiple_queries | 여러 검색어의 랭킹 점수 |

**주의**: 이 테스트들은 `@patch` 데코레이터를 사용하여 Elasticsearch를 모킹합니다.

### ProductRankingAPITests
| 테스트 | 목적 |
|--------|------|
| test_ranking_empty | 데이터 없을 때 빈 리스트 반환 |
| test_ranking_retrieval | 랭킹 데이터 조회 및 정렬 |
| test_ranking_limit_to_10 | 상위 10개만 반환 |
| test_ranking_score_format | 응답 JSON 형식 검증 |

### ProductListAPITests
| 테스트 | 목적 |
|--------|------|
| test_list_products | GET /api/products/items/ 조회 |
| test_retrieve_product | GET /api/products/items/{id}/ 조회 |
| test_create_product_api | POST 상품 생성 |
| test_update_product_api | PUT 상품 수정 |
| test_delete_product_api | DELETE 상품 삭제 |

## 테스트 실행 결과 예상

### 성공 케이스
```
Creating test database for alias 'default'...
Ran 27 tests in 2.345s

OK
```

### 실패 케이스 (Elasticsearch 미연결)
```
ERROR: test_search_with_valid_query (products.tests.ProductSearchAPITests)
...
ConnectionError: Connection refused
```
→ Docker에서 실행하거나 모킹이 제대로 작동하는지 확인하세요.

## 주의사항

1. **TransactionTestCase 사용**
   - `ProductSearchAPITests`는 `TransactionTestCase`를 상속받음
   - 데이터베이스 트랜잭션을 올바르게 처리하기 위함
   - 일반 `TestCase`보다 느릴 수 있음

2. **Redis 초기화**
   - 각 테스트 전에 Redis의 `search_ranking` 키 삭제
   - 테스트 간 격리(isolation) 보장

3. **캐시 초기화**
   - 각 테스트 전에 `cache.clear()` 호출
   - 캐시 관련 테스트의 신뢰성 보장

4. **Elasticsearch 모킹**
   - `@patch` 데코레이터로 ProductDocument.search 모킹
   - 실제 Elasticsearch 연결 필요 없음

## 다음 단계

- 에러 핸들링 테스트 추가 (2단계)
- 통합 테스트 추가 (전체 플로우)
- 성능 테스트 추가 (대량 데이터 검색)
- CI/CD 파이프라인 구성
