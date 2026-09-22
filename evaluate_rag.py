"""
Évaluation automatique du RAG avec Ragas, sur le jeu de test annoté.

Usage :
    uv run python evaluate_rag.py
"""

import sys
import types

# Contournement d'un bug connu de ragas (issue #2753 sur GitHub) : ragas
# importe sans condition ChatVertexAI depuis un chemin supprimé dans les
# versions récentes de langchain-community (>=0.4.2, celle utilisée ici).
# Ce bloc DOIT s'exécuter avant tout import de ragas.
faux_module = types.ModuleType("langchain_community.chat_models.vertexai")
faux_module.ChatVertexAI = None
sys.modules["langchain_community.chat_models.vertexai"] = faux_module

import csv

import numpy as np
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, LLMContextRecall
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings

from src.generation import API_KEY_MISTRAL, construire_chaine_rag

NB_QUESTIONS_GENEREES = 3

PROMPT_PERTINENCE = """Étant donné la réponse ci-dessous, génère {n} questions différentes et plausibles auxquelles cette réponse pourrait correspondre. Réponds uniquement avec les questions, une par ligne, sans numérotation ni aucun autre texte.

Réponse :
{reponse}"""


def construire_dataset_ragas(chemin_testset="data/qa_testset.csv"):
    chaine_rag, retriever = construire_chaine_rag()

    lignes = []
    with open(chemin_testset, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            question = row["question"]
            reference = row["reponse_reference"]

            reponse = appel_avec_retry(chaine_rag.invoke, question)
            documents = appel_avec_retry(retriever.invoke, question)

            lignes.append({
                "user_input": question,
                "response": reponse,
                "retrieved_contexts": [doc.page_content for doc in documents],
                "reference": reference,
            })

    return lignes


def similarite_cosinus(vecteur_a, vecteur_b):
    vecteur_a, vecteur_b = np.array(vecteur_a), np.array(vecteur_b)
    return float(
        np.dot(vecteur_a, vecteur_b)
        / (np.linalg.norm(vecteur_a) * np.linalg.norm(vecteur_b))
    )


def generer_questions_candidates(llm, reponse, n=NB_QUESTIONS_GENEREES):
    resultat = appel_avec_retry(llm.invoke, PROMPT_PERTINENCE.format(n=n, reponse=reponse))
    lignes = [
        ligne.strip("-• ").strip()
        for ligne in resultat.content.split("\n")
        if ligne.strip()
    ]
    return lignes[:n]


def calculer_pertinence_reponse(lignes, llm, embeddings):
    """
    Calcule un score de pertinence question/réponse, en dehors de ragas
    (contourne un bug de ResponseRelevancy incompatible avec Mistral,
    cf. discussion de debug). Même principe que ResponseRelevancy de ragas :
    on régénère des questions à partir de la réponse, et on mesure leur
    similarité avec la question posée.
    """
    scores = []
    for ligne in lignes:
        questions_generees = generer_questions_candidates(llm, ligne["response"])
        if not questions_generees:
            scores.append(float("nan"))
            continue

        emb_question_originale = embeddings.embed_query(ligne["user_input"])
        emb_questions_generees = embeddings.embed_documents(questions_generees)

        similarites = [
            similarite_cosinus(emb_question_originale, e)
            for e in emb_questions_generees
        ]
        scores.append(sum(similarites) / len(similarites))

    return scores


def main():
    lignes = construire_dataset_ragas()
    dataset = EvaluationDataset.from_list(lignes)

    llm_juge = ChatMistralAI(model="ministral-3b-2512", mistral_api_key=API_KEY_MISTRAL)
    embeddings_juge = MistralAIEmbeddings(model="mistral-embed", mistral_api_key=API_KEY_MISTRAL)

    evaluator_llm = LangchainLLMWrapper(llm_juge)
    evaluator_embeddings = LangchainEmbeddingsWrapper(embeddings_juge)

    # ResponseRelevancy est volontairement exclue : incompatible avec
    # ChatMistralAI (TypeError interne à ragas, cf. debug), remplacée par
    # calculer_pertinence_reponse() ci-dessous.
    metriques = [
        Faithfulness(llm=evaluator_llm),
        LLMContextRecall(llm=evaluator_llm),
    ]

    resultats = evaluate(dataset=dataset, metrics=metriques)
    df = resultats.to_pandas()

    df["answer_relevancy"] = calculer_pertinence_reponse(lignes, llm_juge, embeddings_juge)

    df.to_csv("data/ragas_results.csv", index=False)

    print(df[["faithfulness", "context_recall", "answer_relevancy"]].mean())
    print("\nRésultats détaillés enregistrés dans data/ragas_results.csv")

import time


def appel_avec_retry(fonction, *args, max_tentatives=5, delai_initial=5, **kwargs):
    """
    Réessaie un appel API Mistral en cas d'erreur de capacité (429) ou
    d'instabilité réseau, avec un backoff exponentiel. Même logique que
    embeddings_avec_retry() dans src/indexation.py.
    """
    delai = delai_initial
    for tentative in range(1, max_tentatives + 1):
        try:
            return fonction(*args, **kwargs)
        except Exception as erreur:
            if tentative == max_tentatives:
                raise
            print(f"  (tentative {tentative}/{max_tentatives} échouée : {erreur} — nouvel essai dans {delai}s)")
            time.sleep(delai)
            delai *= 2

if __name__ == "__main__":
    main()