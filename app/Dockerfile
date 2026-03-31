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
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install ollama

COPY . .

# Display per Java + MaxEnt
ENV DISPLAY=:99

# Avvia solo Xvfb e tieni il container vivo
CMD ["sh", "-c", "\
Xvfb :99 -screen 0 1024x768x16 & \
sleep infinity \
"]
