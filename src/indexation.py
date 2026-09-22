"""
Construction / reconstruction de l'index vectoriel FAISS à partir des données sources.
"""

import os

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS as LangChainFAISS
from langchain_core.documents import Document
from langchain_mistralai import MistralAIEmbeddings
from mistralai.client import Mistral

from src.generation import CHEMIN_INDEX_PAR_DEFAUT
from src.preparation import charger_df_evenements_final
from src.structuration import construire_metadata, construire_texte

load_dotenv()
API_KEY_MISTRAL = os.getenv("API_KEY_MISTRAL")


def charger_documents(chemin_data: str = "data/data.json") -> list[Document]:
    """Charge et nettoie les événements, construit un Document par événement (sans découpage)."""
    df_evenements_final = charger_df_evenements_final(chemin_data)

    df_evenements_final["texte_embedding"] = df_evenements_final.apply(construire_texte, axis=1)
    df_evenements_final["metadata"] = df_evenements_final.apply(construire_metadata, axis=1)

    documents = [
        Document(page_content=row["texte_embedding"], metadata=row["metadata"])
        for _, row in df_evenements_final.iterrows()
    ]
    return documents


def batcher(iterable, taille=50):
    """Découpe une liste en lots, pour respecter les limites de l'API Mistral."""
    for i in range(0, len(iterable), taille):
        yield iterable[i:i + taille]


def reconstruire_vectorstore(chemin_index: str = CHEMIN_INDEX_PAR_DEFAUT, chemin_data: str = "data/data.json"):
    """Reconstruit l'index FAISS depuis les données sources et le sauvegarde sur disque."""
    client = Mistral(api_key=API_KEY_MISTRAL)
    embedding_model = MistralAIEmbeddings(model="mistral-embed", api_key=API_KEY_MISTRAL)

    documents = charger_documents(chemin_data)
    textes_a_vectoriser = [doc.page_content for doc in documents]

    embeddings = []
    for lot in batcher(textes_a_vectoriser, taille=50):
        reponse = embeddings_avec_retry(client, "mistral-embed", lot)
        embeddings.extend([e.embedding for e in reponse.data])

    vectorstore = LangChainFAISS.from_embeddings(
        text_embeddings=list(zip(textes_a_vectoriser, embeddings)),
        embedding=embedding_model,
        metadatas=[doc.metadata for doc in documents],
    )
    vectorstore.save_local(chemin_index)

    return vectorstore

import time


def embeddings_avec_retry(client, model, inputs, max_tentatives=5, delai_initial=2):
    """Appelle client.embeddings.create avec retry et backoff exponentiel
    sur les erreurs transitoires de l'API (429, 503, timeouts...)."""
    for tentative in range(1, max_tentatives + 1):
        try:
            return client.embeddings.create(model=model, inputs=inputs)
        except Exception as e:
            if tentative == max_tentatives:
                raise
            delai = delai_initial * (2 ** (tentative - 1))  # 2s, 4s, 8s, 16s...
            print(f"Erreur API ({e}), nouvelle tentative dans {delai}s ({tentative}/{max_tentatives})")
            time.sleep(delai)
