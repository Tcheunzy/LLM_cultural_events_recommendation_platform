import os
import json
import pytest
from dotenv import load_dotenv
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

@pytest.fixture(scope="session")
def embedding_model():
    return MistralAIEmbeddings(model="mistral-embed", api_key=os.getenv("API_KEY_MISTRAL"))

@pytest.fixture(scope="session")
def vectorstore(embedding_model):
    return FAISS.load_local(
        "data/index/faiss_vectorstore",
        embeddings=embedding_model,
        allow_dangerous_deserialization=True,
    )

@pytest.fixture(scope="session")
def chunks_indexes(vectorstore):
    # les Document indexés (texte+metadata), extraits du docstore interne du vector store
    return list(vectorstore.docstore._dict.values())

@pytest.fixture(scope="session")
def uids_attendus():
    with open("data/index/uids_attendus.json", encoding="utf-8") as f:
        return json.load(f)