# Test API

PurePick의 API 엔드포인트를 빠르게 테스트합니다.

## 사용법
```
/test-api [endpoint] [options]
```

### 예제
```
/test-api list                    # 모든 상품 조회
/test-api search -q 토너          # 토너 검색
/test-api ranking                 # 인기 검색어 조회
/test-api health                  # 서버 상태 확인
```

---

## 테스트 가능한 엔드포인트

### 1. 상품 조회
```
/test-api list                     # GET /api/products/items/
/test-api get [id]                 # GET /api/products/items/{id}/
```

**응답 확인 항목:**
- HTTP 상태 코드 (200 OK)
- JSON 형식 검증
- 필수 필드 존재 (id, name, brand, ingredients)

---

### 2. 상품 검색 (캐시 포함)
```
/test-api search -q 토너           # GET /api/products/items/search/?q=토너
/test-api search -q 에센스 -v      # 상세 출력 (캐시 상태, 응답 시간)
```

**응답 확인 항목:**
- 검색 결과 개수
- 캐시 히트/미스 여부
- 응답 시간 (ms)
- 결과 관련성

---

### 3. 인기 검색어 조회
```
/test-api ranking                  # GET /api/products/items/ranking/
/test-api ranking -v               # 상세 출력 (순위, 검색 횟수)
```

**응답 확인 항목:**
- 상위 10개 키워드
- 각 키워드 점수
- Redis Sorted Set 동작 확인

---

### 4. 상품 생성/수정/삭제
```
/test-api create                   # POST /api/products/items/ (더미 데이터)
/test-api update [id]              # PATCH /api/products/items/{id}/
/test-api delete [id]              # DELETE /api/products/items/{id}/
```

---

### 5. 서버 상태 확인
```
/test-api health                   # Django 서버 상태 확인
/test-api health -all              # 모든 의존성(DB, ES, Redis) 포함
```

---

## 옵션

- **`-q [query]`**: 검색어 지정
- **`-v`, `--verbose`**: 상세 출력 (응답 헤더, 응답 시간, 캐시 정보)
- **`-pretty`**: JSON 포맷팅
- **`-all`**: 모든 의존성 포함 검사

---

## 출력 형식

### 기본 출력
```
🎯 GET /api/products/items/search/?q=토너
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 200 OK

📊 응답 데이터
├─ 결과 개수: 15개
├─ 응답 시간: 45ms
├─ 캐시: MISS (Elasticsearch 쿼리 실행)
└─ 상위 3개:
   1. 라네즈 에센스 워터 토너
   2. 아모레퍼시픽 에센스 토너
   3. 설화수 진설 토너

```

### 상세 출력 (`-v` 옵션)
```
🎯 GET /api/products/items/search/?q=토너
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 요청 정보
├─ URL: http://localhost:8000/api/products/items/search/?q=토너
├─ 메서드: GET
└─ 타임스탐프: 2026-01-25 15:30:45

✅ 응답 상태
├─ 코드: 200 OK
├─ 응답 시간: 45ms
└─ Content-Type: application/json

💾 캐시 상태
├─ 캐시 상태: MISS
├─ Redis 키: search:토너
└─ TTL: 3600초 (다음 검색부터 캐시됨)

📊 데이터 검증
├─ JSON 형식: ✅ 유효
├─ 필드 검증: ✅ 모두 존재
└─ 스키마: ✅ 일치

🔢 응답 바디
[전체 JSON 출력]
```

---

## 에러 처리

API 호출 실패 시 자동으로:
- 에러 메시지 분석
- 관련 로그 검색
- 해결 방법 제시

예시:
```
❌ 503 Service Unavailable
⚠️ Elasticsearch 서버가 응답하지 않습니다.

📌 원인 분석
1. Elasticsearch 컨테이너 상태 확인 필요
2. 로그: docker-compose logs elasticsearch

✅ 해결 방법
1. docker-compose restart elasticsearch
2. 30초 후 다시 시도
```

