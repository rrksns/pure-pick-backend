# pure-pick-backend
검색'과 '랭킹'을 마이크로하게 구현


pure-pick-backend/          # Root Directory
├── config/                 # Django 프로젝트 설정 (settings.py 등)
├── apps/                   # 비즈니스 로직 (products, search 등 앱 분리)
├── requirements.txt        # 파이썬 패키지 목록
├── Dockerfile              # Django 이미지 빌드 설정
└── docker-compose.yml      # 전체 인프라 오케스트레이션 (가장 중요!)