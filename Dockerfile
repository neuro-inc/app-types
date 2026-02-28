ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

LABEL org.opencontainers.image.source="https://github.com/neuro-inc/app-types"
ARG POETRY_VERSION=2.2.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=0

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY README.md poetry.lock pyproject.toml ./
RUN pip --no-cache-dir install "poetry==${POETRY_VERSION}" && poetry install -E fixtures --no-root --no-cache

COPY src ./src
COPY fixtures ./fixtures
RUN poetry install -E fixtures --only-root --no-cache

ENTRYPOINT ["app-types"]
