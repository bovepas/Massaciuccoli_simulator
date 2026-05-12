FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    default-jre \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DISPLAY=:99

CMD ["sh", "-c", "\
Xvfb :99 -screen 0 1024x768x16 & \
python -m versions.v6_1_orchestrator \
"]