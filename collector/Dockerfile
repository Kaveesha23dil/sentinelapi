FROM python:3.12.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app:/app/collector
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ /app/
COPY collector/ /app/collector/
RUN useradd --create-home --uid 10002 sentinelapi && mkdir /spool /state && chown sentinelapi:sentinelapi /spool /state
USER sentinelapi
CMD ["python", "-m", "traffic_collector.main"]
