# Imagen oficial de uv con Python 3.12
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Compilar a bytecode al instalar y copiar los paquetes en lugar de linkearlos
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Primero solo las dependencias: si no cambian, Docker reutiliza esta capa
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

COPY src ./src

WORKDIR /app/src

EXPOSE 8000

CMD ["sh", "-c", "uv run --no-sync manage.py migrate && uv run --no-sync manage.py runserver 0.0.0.0:8000"]
