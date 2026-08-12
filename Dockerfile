FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY README.md ./
COPY src ./src
COPY configs ./configs
RUN uv sync --frozen

ENTRYPOINT ["uv", "run", "debatebench", "run"]
CMD ["configs/example.yaml"]
