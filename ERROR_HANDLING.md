# Error Handling & Input Validation Guide

이 문서는 PurePick 프로젝트의 에러 핸들링 및 입력 검증 전략을 설명합니다.

## 개요

프로덕션 환경의 안정성을 위해 다음을 구현했습니다:

- 구조화된 로깅 (Logging)
- 포괄적인 예외 처리
- 사용자 친화적인 에러 응답
- 입력값 검증
- 서비스 연결 오류 처리

---

## 로깅 시스템

### 로깅 레벨

| 레벨 | 사용 사례 | 예시 |
|------|---------|------|
| DEBUG | 상세 개발 정보 | 캐시 조회 결과, DB 쿼리 |
| INFO | 주요 작업 흐름 | 캐시 히트/미스, 검색 완료 |
| WARNING | 예상된 오류 상황 | 캐시 조회 실패, Redis 일시적 오류 |
| ERROR | 심각한 오류 | Elasticsearch 연결 실패 |
| CRITICAL | 시스템 중단 | (현재 미사용) |

### 로그 파일

```
logs/django.log  # 프로덕션 로그 (Rotating)
```

- 최대 크기: 10MB
- 백업 파일: 5개까지 보관
- 자동 순환 (Rotating File Handler)

### 로깅 설정 (settings.py)

```python
LOGGING = {
    'loggers': {
        'products': {  # products 앱 로거
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}
```

### 예제: 로그 출력

```python
import logging
logger = logging.getLogger(__name__)

# 검색 API
logger.info(f"캐시 히트: {query}")
logger.warning(f"캐시 조회 실패: {str(e)}")
logger.error(f"Elasticsearch 연결 실패: {str(e)}")
```

---

## 예외 처리 전략

### 1. 검색 API (`search` 엔드포인트)

#### 계층별 예외 처리

```
Input Validation (400)
     ↓
Redis Cache (Warning → Continue)
     ↓
Elasticsearch (503 or 500)
     ↓
Database Query (500)
     ↓
Cache Write (Warning → Continue)
     ↓
Ranking Update (Warning → Continue)
```

#### 에러 응답 사례

**입력값 검증 실패 (400)**
```json
{
  "error": "검색어는 100자 이하여야 합니다."
}
```

**Elasticsearch 연결 실패 (503)**
```json
{
  "error": "Elasticsearch 서비스에 연결할 수 없습니다.",
  "detail": "검색 기능을 일시적으로 사용할 수 없습니다."
}
```

**예상치 못한 오류 (500)**
```json
{
  "error": "예상치 못한 오류가 발생했습니다.",
  "detail": "[상세 에러 메시지]"
}
```

### 2. 랭킹 API (`ranking` 엔드포인트)

**Redis 연결 실패 (503)**
```json
{
  "error": "Redis 서비스에 연결할 수 없습니다.",
  "detail": "인기 검색어 기능을 일시적으로 사용할 수 없습니다."
}
```

---

## 입력값 검증

### 검색어 (q 파라미터)

| 규칙 | 정책 |
|------|------|
| 필수 | 빈 문자열은 400 에러 |
| 공백 제거 | `.strip()` 적용 |
| 최대 길이 | 100자 (초과 시 400 에러) |
| 특수문자 | 제한 없음 (Elasticsearch에서 처리) |

### 예제

```python
query = request.query_params.get('q', '').strip()

if not query:
    return Response(
        {'error': '검색어를 입력해주세요.'},
        status=status.HTTP_400_BAD_REQUEST
    )

if len(query) > 100:
    return Response(
        {'error': '검색어는 100자 이하여야 합니다.'},
        status=status.HTTP_400_BAD_REQUEST
    )
```

---

## 주요 예외 타입 및 처리

### Elasticsearch 예외

```python
from elasticsearch.exceptions import ConnectionError as ESConnectionError

try:
    search_result = ProductDocument.search().query(q)
except ESConnectionError:
    # 연결 실패 → 503 Service Unavailable
    return Response(..., status=503)
except Exception:
    # 기타 오류 → 500 Internal Server Error
    return Response(..., status=500)
```

### Redis 예외

```python
from redis.exceptions import ConnectionError as RedisConnectionError

try:
    con = get_redis_connection("default")
    con.zincrby("search_ranking", 1, keyword)
except RedisConnectionError:
    # 로그만 기록하고 계속 진행
    logger.error(f"Redis 연결 실패: {str(e)}")
```

### Cache 예외

```python
try:
    cached_result = cache.get(cache_key)
except Exception as e:
    # 캐시 실패해도 Elasticsearch 검색 진행
    logger.warning(f"캐시 조회 실패: {str(e)}")
```

---

## 테스트

### 에러 핸들링 테스트 클래스

**ProductSearchErrorHandlingTests**
- ✅ 검색어 길이 초과
- ✅ 공백만 입력
- ✅ Elasticsearch 연결 실패
- ✅ Elasticsearch 일반 오류
- ✅ 검색 결과 없음
- ✅ Redis 연결 실패 (검색은 계속 진행)

**ProductRankingErrorHandlingTests**
- ✅ Redis 연결 실패
- ✅ Redis 일반 오류

### 테스트 실행

```bash
# 에러 핸들링 테스트만
docker-compose exec web python manage.py test products.tests.ProductSearchErrorHandlingTests products.tests.ProductRankingErrorHandlingTests --verbosity=2

# 모든 테스트
docker-compose exec web python manage.py test products.tests --verbosity=2
```

---

## 베스트 프랙티스

### 1. 부가 기능은 실패해도 계속 진행

```python
# ❌ 나쁜 예: 랭킹 실패로 인해 검색이 실패
def search(self, request):
    results = search_elasticsearch()
    self._add_ranking(query)  # 실패하면 검색도 실패
    return Response(results)

# ✅ 좋은 예: 랭킹 실패는 로그만 기록
def search(self, request):
    results = search_elasticsearch()
    try:
        self._add_ranking(query)
    except Exception as e:
        logger.error(f"랭킹 업데이트 실패: {str(e)}")
    return Response(results)
```

### 2. 사용자 친화적인 메시지

```python
# ❌ 나쁜 예: 기술적 오류 노출
return Response({'error': 'ConnectionError: Connection refused'})

# ✅ 좋은 예: 이해하기 쉬운 메시지
return Response({
    'error': 'Elasticsearch 서비스에 연결할 수 없습니다.',
    'detail': '검색 기능을 일시적으로 사용할 수 없습니다.'
})
```

### 3. 적절한 HTTP 상태 코드

```python
400  # Bad Request (입력값 오류)
503  # Service Unavailable (외부 서비스 오류)
500  # Internal Server Error (서버 오류)
```

### 4. 구조화된 로깅

```python
# ❌ 나쁜 예: print 사용
print(f"Search failed: {error}")

# ✅ 좋은 예: logger 사용
logger.error(f"검색 실패: {error}")
```

---

## 트러블슈팅

### 문제: "Elasticsearch 서비스에 연결할 수 없습니다"

**원인**
- Elasticsearch 서비스 다운
- 네트워크 연결 문제

**해결**
```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs elasticsearch

# 재시작
docker-compose restart elasticsearch
```

### 문제: "Redis 서비스에 연결할 수 없습니다"

**원인**
- Redis 서비스 다운
- 메모리 부족

**해결**
```bash
# Redis 상태 확인
docker-compose exec redis redis-cli ping

# 로그 확인
docker-compose logs redis

# 재시작
docker-compose restart redis
```

### 문제: 캐시가 작동하지 않음

**확인 사항**
```bash
# Redis 메모리 사용량
docker-compose exec redis redis-cli INFO memory

# 캐시 키 확인
docker-compose exec redis redis-cli KEYS "search:*"

# 캐시 데이터 조회
docker-compose exec redis redis-cli GET "search:토너"
```

---

## 다음 단계

- [ ] 메트릭 수집 (Prometheus)
- [ ] 에러 추적 (Sentry)
- [ ] 알림 설정 (Slack 통지)
- [ ] 회로 차단기 패턴 (Circuit Breaker) 구현
