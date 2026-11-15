FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    openssh-client \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir opencv-python-headless numpy yt-dlp

WORKDIR /app

COPY pi/live.py /app/pi/
COPY pi/models /app/pi/models
COPY pi/centroids.npz /app/pi/

ENV REPO=/repo

CMD ["python", "-u", "/app/pi/live.py"]
