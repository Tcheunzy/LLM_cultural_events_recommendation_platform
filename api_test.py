# api_test.py
"""
Tests fonctionnels de l'API REST (endpoints /, /health, /ask, /rebuild),
via le TestClient de FastAPI. Contrairement à tests/test_generation.py qui
teste la chaîne RAG directement en Python, ce fichier teste l'API HTTP
telle qu'un appelant externe l'utiliserait.

Usage :
    uv run pytest api_test.py -v
"""

import os

import pytest
from fastapi.testclient import TestClient

from api.main import app

pytestmark = pytest.mark.skipif(
    not os.getenv("API_KEY_MISTRAL"),
    reason="API_KEY_MISTRAL non définie, tests d'intégration ignorés",
)

REBUILD_TOKEN = os.getenv("REBUILD_TOKEN")


@pytest.fixture(scope="module")
def client():
    # Le "with" déclenche le lifespan (chargement de la chaîne RAG au démarrage)
    with TestClient(app) as c:
        yield c


def test_root(client):
    reponse = client.get("/")
    assert reponse.status_code == 200


def test_health(client):
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json()["status"] == "healthy"


def test_ask_question_valide(client):
    reponse = client.post("/ask", json={"question": "Quand se déroule le Fest deizh à Saint-M'Hervé ?"})
    assert reponse.status_code == 200
    corps = reponse.json()
    assert "response" in corps
    assert corps["response"].strip() != ""


def test_ask_question_vide(client):
    reponse = client.post("/ask", json={"question": "   "})
    assert reponse.status_code == 400


def test_ask_champ_manquant(client):
    reponse = client.post("/ask", json={})
    assert reponse.status_code == 422  # validation Pydantic automatique


def test_ask_mauvais_type(client):
    reponse = client.post("/ask", json={"question": 12345})
    assert reponse.status_code == 422


def test_rebuild_sans_token(client):
    reponse = client.post("/rebuild")
    assert reponse.status_code == 422  # header requis manquant (vu tout à l'heure)


def test_rebuild_mauvais_token(client):
    reponse = client.post("/rebuild", headers={"X-Admin-Token": "mauvaise-valeur"})
    assert reponse.status_code == 403


@pytest.mark.skipif(
    not REBUILD_TOKEN or not os.getenv("RUN_SLOW_TESTS"),
    reason="Reconstruction complète de l'index désactivée par défaut (coûteuse en appels API) "
           "— définir RUN_SLOW_TESTS=1 pour l'activer",
)
def test_rebuild_avec_bon_token(client):
    reponse = client.post("/rebuild", headers={"X-Admin-Token": REBUILD_TOKEN})
    assert reponse.status_code == 200
    assert reponse.json()["status"] == "base vectorielle reconstruite"