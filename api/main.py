from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from src.generation import construire_chaine_rag
from src.indexation import reconstruire_vectorstore  
import os

etat = {}
REBUILD_TOKEN = os.getenv("REBUILD_TOKEN")

@asynccontextmanager
async def lifespan(app: FastAPI):
    etat["chaine_rag"], etat["retriever"] = construire_chaine_rag()
    yield
    etat.clear()

app = FastAPI(title="Puls-Events RAG API", lifespan = lifespan)


class Question(BaseModel):
    question: str

@app.get("/", tags=["Monitoring"])
def root():
    return {"message" : "API RAG LLM evenement culturel en Bretagne 2026"}

@app.get("/health", tags=["Health"])
def health():
    return {"status" : "healthy"}

@app.post("/ask")
def ask(payload : Question):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail = "question manquante")
    response = etat["chaine_rag"].invoke(payload.question)
    return {"response" : response}


def verifier_token_admin(x_admin_token: str = Header(...)):
    if not REBUILD_TOKEN or x_admin_token != REBUILD_TOKEN:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
@app.post("/rebuild", dependencies=[Depends(verifier_token_admin)])
def rebuild():
    reconstruire_vectorstore() # relit les données sources, ré-embedde, sauvegarde sur disque
    etat["chaine_rag"], etat["retriever"] = construire_chaine_rag() # recharge la version fraîche
    return {"status": "base vectorielle reconstruite"}



