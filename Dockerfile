FROM python:3.11-slim

COPY src/vasiniyo_media_loader /vasiniyo_media_loader
COPY requirements.txt .

ENV DENO_INSTALL=/usr/local

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates unzip xz-utils \
    && curl -L -o ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    && tar -xJf ffmpeg.tar.xz \
    && mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ \
    && chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe \
    && rm -rf ffmpeg-*-amd64-static ffmpeg.tar.xz \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://deno.land/install.sh | sh \
    && mkdir -p /logs /download /.cache \
    && chmod 777 /.cache

RUN --mount=type=cache,target=/.cache/pip \
    pip install -r requirements.txt

VOLUME "/logs/logs.log"
VOLUME "/ytloads"
VOLUME "/run/user/1000/bus"
VOLUME "/cookies.txt"
WORKDIR /

CMD ["python3", "-u", "-m", "vasiniyo_media_loader"]
