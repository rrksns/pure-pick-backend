# Search Logs

Docker 컨테이너 로그에서 특정 패턴이나 키워드를 검색합니다.

## 사용법
```
/search-logs [keyword] [options]
```

### 예제
```
/search-logs error              # 모든 컨테이너에서 "error" 검색
/search-logs elasticsearch error # elasticsearch 컨테이너에서 "error" 검색
/search-logs redis warning      # redis 컨테이너에서 "warning" 검색
/search-logs db "Connection refused"  # MySQL에서 연결 거부 에러 검색
```

---

## 검색 대상 컨테이너

| 컨테이너 | 포트 | 주요 에러 패턴 |
|---------|------|----------------|
| `web` (Django) | 8000 | Error, Exception, Traceback, FAILED |
| `db` (MySQL) | 3306 | ERROR, refused, timeout, cannot connect |
| `elasticsearch` | 9200 | ERROR, exception, failed, connection |
| `redis` | 6379 | error, connection, timeout, WRONGTYPE |
| `kibana` | 5601 | error, warning, exception |

---

## 검색 옵션

- **`--container [name]`** 또는 **`-c [name]`**: 특정 컨테이너만 검색
  ```
  /search-logs error --container web
  ```

- **`--lines [number]`** 또는 **`-n [number]`**: 최근 N줄만 검색 (기본값: 100)
  ```
  /search-logs error --lines 50
  ```

- **`--case-sensitive`**: 대소문자 구분 검색
  ```
  /search-logs Error --case-sensitive
  ```

- **`--follow`** 또는 **`-f`**: 실시간 로그 추적 (Ctrl+C로 중지)
  ```
  /search-logs error --follow
  ```

---

## 출력 형식

```
🔍 "error" 검색 결과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 web (Django)
├─ [2026-01-25 10:15:23] ERROR: Connection to Elasticsearch failed
├─ [2026-01-25 10:14:56] ERROR: Timeout connecting to Redis
└─ 2개 일치

🗄️ db (MySQL)
├─ [2026-01-25 10:10:15] ERROR 1045: Access denied for user 'root'
└─ 1개 일치

📊 elasticsearch
├─ [2026-01-25 09:50:32] [ERROR] Connection pool exhausted
└─ 1개 일치

총 4개 결과 발견
```

---

## 자주 사용되는 검색어

- **`error`** - 모든 에러 메시지
- **`warning`** - 경고 메시지
- **`connection`** - 연결 관련 이슈
- **`timeout`** - 타임아웃 이슈
- **`Traceback`** - Python 예외 발생
- **`refused`** - 연결 거부
- **`migrate`** - 마이그레이션 관련

