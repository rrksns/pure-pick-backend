# Python 3.11 (최신 안정 버전)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필수 패키지 설치 (MySQL 클라이언트 등)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# 프로젝트 코드 복사
COPY . /app/

# 실행 명령어 (docker-compose에서 오버라이딩 됨)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]