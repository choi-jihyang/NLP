# 학생 코드 실행용 이미지 (C · Python). 빌드: docker build -t thinkguard-runner backend/sandbox
FROM python:3.12-slim

# C 컴파일러. 빌드할 때만 인터넷이 필요하고, 실행할 때 컨테이너는 --network none이다
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# 읽기 전용 파일 시스템에서 .pyc를 쓰려다 실패하지 않게
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# root가 아닌 실행 전용 사용자
RUN useradd --create-home --uid 10001 runner

COPY harness.py /opt/runner/harness.py

USER runner
WORKDIR /tmp
ENTRYPOINT ["python", "-I", "/opt/runner/harness.py"]
