# tests/test_generation.py
import os
import pytest
from src.generation import construire_chaine_rag

# Les tests appellent l'API Mistral : on les saute si la clé n'est pas dispo
# (ex : dans un environnement CI sans secret configuré)
pytestmark = pytest.mark.skipif(
    not os.getenv("API_KEY_MISTRAL"),
    reason="API_KEY_MISTRAL non définie, tests d'intégration ignorés",
)


@pytest.fixture(scope="module")
def chaine_rag():
    # Construite une seule fois pour tout le fichier de tests
    chaine, _ = construire_chaine_rag()
    return chaine


def test_chaine_repond_sans_erreur(chaine_rag):
    """La chaîne doit s'exécuter sans lever d'exception sur une question valide."""
    reponse = chaine_rag.invoke("Quand se déroule le Fest deizh à Saint-M'Hervé ?")
    contenu = reponse.content if hasattr(reponse, "content") else reponse
    assert isinstance(contenu, str)


def test_reponse_non_vide(chaine_rag):
    """La réponse générée ne doit jamais être vide ou uniquement des espaces."""
    reponse = chaine_rag.invoke("Quel événement a lieu à Brest en mai 2026 ?")
    contenu = reponse.content if hasattr(reponse, "content") else reponse
    assert contenu.strip() != ""


def test_anti_hallucination(chaine_rag):
    """
    Sur une question hors périmètre (Nantes = hors Bretagne), le chatbot doit
    indiquer l'absence d'information plutôt qu'inventer un événement.
    """
    reponse = chaine_rag.invoke(
        "Quels événements de la Fête de la Bretagne sont prévus à Nantes en 2026 ?"
    )
    contenu = (reponse.content if hasattr(reponse, "content") else reponse).lower()

    marqueurs_refus = [
        "aucune information",
        "ne dispose pas",
        "pas d'événement",
        "je n'ai pas trouvé",
        "aucun événement",
        "hors de mon périmètre",
    ]
    assert any(marqueur in contenu for marqueur in marqueurs_refus), (
        f"Réponse ne semble pas indiquer une absence d'information : {contenu}"
    )