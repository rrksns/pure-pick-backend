# pure-pick-backend
검색'과 '랭킹'을 마이크로하게 구현


pure-pick-backend/          # Root Directory
├── config/                 # Django 프로젝트 설정 (settings.py 등)
├── apps/                   # 비즈니스 로직 (products, search 등 앱 분리)
├── requirements.txt        # 파이썬 패키지 목록
├── Dockerfile              # Django 이미지 빌드 설정
└── docker-compose.yml      # 전체 인프라 오케스트레이션 (가장 중요!)



# 💄 PurePick (화장품 성분 분석 및 검색 서비스)

> **Elasticsearch**와 **Redis**를 활용한 고성능 화장품 검색 API 서버입니다.  
> 대용량 데이터 환경에서도 빠른 검색 속도와 실시간 검색어 랭킹 기능을 제공합니다.

## 🛠 Tech Stack (기술 스택)

- **Backend:** Python 3.11, Django REST Framework
- **Database:** MySQL 8.0 (RDB), Elasticsearch 7.17 (Search Engine)
- **Cache:** Redis (Caching & Ranking)
- **Infra:** Docker, Docker Compose

## 🏛 System Architecture (아키텍처)

1. **MySQL:** 화장품, 브랜드, 성분 데이터의 원본 저장소 (RDB)
2. **Elasticsearch:** 역정규화된 문서 구조를 통한 고속 텍스트 검색 및 필터링
3. **Redis:**
    - **Cache:** 검색 결과 캐싱 (Look-aside 패턴, TTL 1시간)
    - **Ranking:** Sorted Set을 활용한 실시간 인기 검색어 집계

## 🚀 Key Features (핵심 기능)

- **고속 검색:** Elasticsearch의 `Multi-match` 쿼리를 활용한 상품/브랜드/성분 통합 검색
- **오타 보정:** Fuzzy Search를 적용하여 '토너'를 '투너'로 검색해도 결과 반환
- **성능 최적화:** Redis 캐싱을 통해 중복 요청 응답 속도 **0.001ms** 달성
- **실시간 트렌드:** 검색어 집계 시스템을 통한 실시간 인기 순위 제공
- **자동화된 문서:** Swagger UI를 통한 API 명세서 제공

## 💻 How to Run (실행 방법)

```bash
# 1. 프로젝트 클론
git clone [https://github.com/사용자아이디/pure-pick-backend.git](https://github.com/사용자아이디/pure-pick-backend.git)

# 2. 실행 (Docker 환경)
docker-compose up -d --build

# 3. 데이터 시딩 (더미 데이터 100개 생성)
docker-compose exec web python manage.py seed_data

# 4. 검색 인덱스 생성
docker-compose exec web python manage.py search_index --rebuild