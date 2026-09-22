"""
Interface Streamlit pour Puls-Events — interroge l'API FastAPI (api/main.py),
qui doit être lancée séparément.

Usage :
    uv run streamlit run streamlit_app.py
"""

import requests
import streamlit as st

URL_API = "http://localhost:8000/ask"

st.set_page_config(page_title="Puls-Events", page_icon="🎭")
st.title("Puls-Events — Assistant événements culturels en Bretagne")
st.caption("Pose une question sur les événements culturels en Bretagne, l'assistant s'appuie sur la base d'événements Open Agenda.")

if "historique" not in st.session_state:
    st.session_state.historique = []  # liste de tuples (question, reponse)

# Affichage de l'historique existant
for question, reponse in st.session_state.historique:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.write(reponse)

# Zone de saisie (en bas de page, envoi sur Entrée)
question = st.chat_input("Pose ta question sur un événement en Bretagne...")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Recherche en cours..."):
            donnees = None
            try:
                reponse_api = requests.post(
                    URL_API, json={"question": question}, timeout=60
                )
                reponse_api.raise_for_status()
                donnees = reponse_api.json()
                reponse = donnees["response"]  # ⚠️ à vérifier/adapter, voir remarque ci-dessous
            except requests.exceptions.ConnectionError:
                reponse = "Impossible de contacter l'API. Est-elle bien lancée sur le port 8000 ?"
            except requests.exceptions.Timeout:
                reponse = "L'API met trop de temps à répondre (timeout). Réessaie."
            except requests.exceptions.HTTPError as erreur:
                if reponse_api.status_code == 400:
                    reponse = "La question ne peut pas être vide."
                else:
                    reponse = f"Erreur de l'API ({reponse_api.status_code}) : {erreur}"
            except KeyError:
                reponse = f"Réponse inattendue de l'API : {donnees}"

        st.write(reponse)

    st.session_state.historique.append((question, reponse))