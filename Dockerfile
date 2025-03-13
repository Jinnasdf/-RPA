# 1️⃣ Python 3.9 Slim 이미지를 사용하여 경량화
FROM python:3.9-slim

# 2️⃣ 작업 디렉토리 설정
WORKDIR /app

# 3️⃣ 필수 패키지 설치 (requirements.txt 이용)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip  # 최신 pip 설치
RUN pip install --no-cache-dir -r requirements.txt  # Flask 및 의존성 설치

# 4️⃣ main.py 복사
COPY main.py .

# 5️⃣ Cloud Run이 사용하는 포트 8080 노출  
EXPOSE 8080  

# 6️⃣ 실행 명령어 (Cloud Run이 실행할 기본 명령어)
CMD ["python", "main.py"]
