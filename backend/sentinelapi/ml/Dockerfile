FROM python:3.12.14-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app:/app/collector
COPY backend/requirements*.txt /app/
RUN pip install --no-cache-dir -r requirements-ml.txt
COPY backend/ /app/
COPY collector/ /app/collector/
RUN useradd --create-home --uid 10002 sentinelapi
USER sentinelapi
CMD ["python", "-m", "sentinelapi.detection.worker"]
