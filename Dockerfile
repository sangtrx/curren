FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CURREN_DB_PATH=/data/curren.db \
    CURREN_API_HOST=0.0.0.0 \
    CURREN_API_PORT=8000

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 curren \
    && mkdir -p /data \
    && chown -R curren:curren /data /app

USER curren

EXPOSE 8000

CMD ["curren-api"]
