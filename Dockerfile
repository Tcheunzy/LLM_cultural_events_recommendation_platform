FROM python:3.12-slim

WORKDIR /app

# uv est utilisé pour installer les dépendances, comme en local
RUN pip install --no-cache-dir uv

# Copiés en premier pour profiter du cache Docker : si le code change mais
# pas les dépendances, cette étape (la plus longue) n'est pas refaite
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Code source de l'API/RAG, et l'index déjà construit (cf. build_index.py)
COPY src/ ./src/
COPY api/ ./api/
COPY data/ ./data/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]