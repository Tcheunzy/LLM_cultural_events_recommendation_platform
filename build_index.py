"""
Script de build de l'index vectoriel FAISS, à exécuter localement AVANT de
construire l'image Docker. L'index généré est ensuite copié dans l'image
(voir Dockerfile) plutôt que reconstruit pendant le build, pour ne pas
dépendre d'une clé API ou d'une connexion réseau à ce moment-là.

"""

from src.indexation import reconstruire_vectorstore

if __name__ == "__main__":
    reconstruire_vectorstore()
    print("Index vectoriel reconstruit avec succès dans data/index/faiss_vectorstore.")