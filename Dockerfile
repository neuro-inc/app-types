FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY README.md ./
COPY setup.cfg ./
COPY setup.py ./
COPY src ./src
RUN pip install --no-cache-dir .

WORKDIR /app/src/apolo_app_types
RUN chmod +x cli.py

ENTRYPOINT ["python", "-m", "cli"]
