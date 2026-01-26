# Check Health

PurePick 프로젝트의 모든 서비스(Docker, Elasticsearch, Redis, MySQL) 상태를 한 번에 확인합니다.

## 사용법
```
/check-health
```

---

## 상태 확인 프로세스

다음 항목들을 순서대로 확인합니다:

### 1. Docker 컨테이너 상태
- `web` (Django 8000)
- `db` (MySQL 3306)
- `elasticsearch` (ES 9200)
- `redis` (Redis 6379)
- `kibana` (Kibana 5601, 선택사항)

**확인 내용**: 각 컨테이너의 상태(running/healthy/exited)

### 2. MySQL 연결 확인
- 데이터베이스 접근 가능 여부
- 마이그레이션 상태
- 테이블 생성 여부

### 3. Elasticsearch 클러스터 상태
- 클러스터 헬스 (green/yellow/red)
- 활성 인덱스 목록
- `products` 인덱스 문서 개수

### 4. Redis 상태
- Redis 서버 연결 가능 여부
- 캐시 데이터 개수
- 검색 랭킹 데이터 개수 (Sorted Set)

### 5. Django 애플리케이션 상태
- 설정 파일 로드 확인
- 캐시 백엔드 연결 확인

---

## 출력 형식

```
🐳 Docker 상태
├─ web: running ✅
├─ db: healthy ✅
├─ elasticsearch: healthy ✅
├─ redis: running ✅
└─ kibana: running ✅

🗄️ MySQL
├─ 연결: 성공 ✅
├─ 마이그레이션: 적용됨 ✅
└─ 테이블: 8개 ✅

🔍 Elasticsearch
├─ 클러스터 상태: green ✅
├─ products 인덱스: 존재 ✅
└─ 문서 수: 100개

💾 Redis
├─ 연결: 성공 ✅
├─ 캐시 키: 5개
└─ 검색 랭킹: 12개

🎯 Django 애플리케이션
├─ 설정 로드: 성공 ✅
└─ 캐시 백엔드: 연결됨 ✅
```

---

## 문제 해결 가이드

**문제 발견 시 자동으로 다음 단계 제시:**
- 해당 서비스의 로그 확인 방법
- 빠른 재시작 명령어
- 상세 진단 방법

