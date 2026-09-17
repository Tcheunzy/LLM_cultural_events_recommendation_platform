# src/generation.py
"""
Construction de la chaîne RAG (retriever + prompt système + LLM) pour Puls-Events.

Ce module extrait dans un fichier importable ce qui vivait jusqu'ici dans les
cellules du notebook, pour permettre aux tests pytest (tests/test_generation.py)
d'instancier la chaîne sans dépendre de Jupyter.
"""

import os

from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()
API_KEY_MISTRAL = os.getenv("API_KEY_MISTRAL")


SYSTEM_PROMPT = """ 
#RÔLE :
Tu es un assistant spécialisé dans les événements culturels en Brtagne. 
Ton rôle est d'aider les utilisateurs à trouver des événements correspondant à leur demande, en te basant uniquement sur les informations fournies dans le contexte ci-dessous.

# OBJECTIF
Tu dois fournir des informations précises liés à l'événement ou aux événements correspondant à la demande des utilisateurs (titre de l'événement, dates, lieu, conditions d'inscriptions.

# REGLES A RESPECTER STRICTEMENT
N'utilises que les informations contenues dans les chunks que tu reçois dans le contexte fourni. N'invente jamais une information qui n'y figure pas.
Si le contexte ne contient pas l'information demandée, dis le clairement plutôt que de deviner. Par exemple : "Je n'ai pas trouvé l'information demandé dans ma base d'événement."
Si la question porte sur un sujet extérieur aux événements culturels bretons (une biographie, une ville en général, une association en dehors de ce contexte, etc.), précise poliment que cette information ne fait pas partie de ta base de connaissance, sans essayer d'y répondre à partir de connaissances générales.
Réponds toujours en français, de façon claire et concise.
Si plusieurs événements correspondent à la demande, présente-les brièvement plutôt que de n'en choisir qu'un arbitrairement.
N'hésite pas à préciser les informations pratiques utiles (dates, lieu, accessibilité, contact) quand elles sont pertinentes pour la question posée.

#EXEMPLE D'INTERACTION GUIDEE :
Utilisateur : "Quel événement culturel maritime a lieu à Concarneau en juillet ?" 
Assistant attendu : " Bonjour, en juillet, à Concarneau, vous pouvez participer aux filets bleus, dans la ville-close le 15 juillet. La participation à cet événement est gratuit et débutera à partir de 12h."


Contexte : 
{context}"""

CHEMIN_INDEX_PAR_DEFAUT = "data/index/faiss_vectorstore"


def charger_vectorstore(chemin_index: str = CHEMIN_INDEX_PAR_DEFAUT) -> FAISS:
    """Recharge l'index FAISS depuis le disque (pas de ré-embedding)."""
    embedding_model = MistralAIEmbeddings(
        model="mistral-embed",
        mistral_api_key=API_KEY_MISTRAL,
    )
    return FAISS.load_local(
        chemin_index,
        embedding_model,
        allow_dangerous_deserialization=True,
    )


def construire_chaine_rag(vectorstore: FAISS | None = None, k: int = 3):
    """
    Construit (retriever, chaine_rag) prêts à l'emploi.

    Si `vectorstore` n'est pas fourni, il est rechargé depuis le disque
    via charger_vectorstore().
    """
    if vectorstore is None:
        vectorstore = charger_vectorstore()

    retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    llm = ChatMistralAI(
        model="ministral-3b-2512",
        mistral_api_key=API_KEY_MISTRAL,
        max_tokens=800,  
    )

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{question}"),
        ]
    )

    # Création d'une fonction permettant de récupérer les chunks obtenus via le
    # retriever et d'assembler le texte de chaque chunk (page_content donc
    # séparation des métadatas), mais en les séparant par une ligne vide
    # (pour compréhension par le LLM).
    def formater_contexte(documents):
        return "\n\n".join(doc.page_content for doc in documents)

    # Instanciation de la chaine RAG
    chaine_rag = (
        {"context": retriever | formater_contexte, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    return chaine_rag, retriever