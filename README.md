Puls-Events — Assistant RAG pour les événements culturels en Bretagne

Projet 9 de la formation Data Science. Puls-Events est un système de Retrieval-Augmented Generation (RAG) qui répond en langage naturel à des questions sur les événements culturels bretons, à partir d'une base de données Open Agenda. L'objectif est de fournir des réponses précises et vérifiables, sans jamais inventer un événement qui n'existe pas dans la base.

Sommaire
Architecture
Données
Choix techniques
Installation
Utilisation
API
Tests
Évaluation
Limites connues
Structure du projet
Pistes d'amélioration
Architecture

Afficher l'image

Diagramme de composants UML — source éditable dans docs/architecture.puml.

Interface Streamlit (streamlit_app.py) : historique de conversation, appelle l'API en HTTP.
API FastAPI (api/main.py) : expose /health, /ask, /rebuild (protégé par token) et /metadata, route les questions vers la chaîne RAG.
Chaîne RAG (src/generation.py) : assemble le retriever FAISS (k=3), le prompt système anti-hallucination et le LLM via LangChain LCEL.
Pipeline de données (src/preparation.py, src/indexation.py) : nettoie, déduplique et vectorise les événements pour construire/reconstruire l'index FAISS.
API Mistral (externe) : mistral-embed pour les embeddings, ministral-3b-2512 pour la génération.

L'ensemble (API + dépendances + index vectoriel pré-construit) est conteneurisé via Docker pour une exécution reproductible en local (voir Utilisation).

Données
Source : Open Agenda, événements culturels en Bretagne.
Pipeline de préparation (src/preparation.py) : filtrage sur le statut de publication, déduplication, fenêtre temporelle glissante de 365 jours, exclusion de mots-clés indésirables, nettoyage du texte (src/nettoyage.py), filtrage des descriptions trop courtes (< 36 caractères).
Volume final : 1651 événements après nettoyage. Longueur du texte vectorisé (texte_embedding) : de 227 à 7531 caractères (moyenne ≈ 1055 caractères) ; 110 événements dépassent 2000 caractères, 9 dépassent 4000 caractères.
Indexation (src/indexation.py) : chaque événement devient un unique Document LangChain (titre + description + métadonnées pratiques), embeddé avec mistral-embed et stocké dans un index FAISS (data/index/faiss_vectorstore).
Choix techniques

Chunking — 1 événement = 1 document, sans découpage supplémentaire. Un premier essai avec RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100) fragmentait 916 des 1651 événements (> 55 %) en un chunk principal (titre + description + lieu) et un chunk résiduel de 120 à 140 caractères ne contenant que des métadonnées pratiques (dates, conditions, accessibilité, âge), sans titre ni description — le chatbot répondait alors parfois "titre non précisé" sur des événements dont seul ce chunk résiduel avait été récupéré par similarité. Retenir l'événement entier comme unique chunk règle ce problème ; la longueur maximale observée (7531 caractères) reste largement compatible avec la fenêtre de contexte de mistral-embed.

Retriever — k = 3, déterminé par la méthode du coude plutôt que fixé arbitrairement.

Génération — ministral-3b-2512, max_tokens = 800. Les modèles mistral-small-latest et mistral-medium-latest renvoyaient systématiquement des erreurs 429 (rate limit), incompatibles avec le plan gratuit Mistral utilisé pour ce projet. ministral-3b-2512 fonctionne de façon stable. max_tokens a été relevé à 800 après que le passage à des chunks plus longs (suite à la correction du chunking ci-dessus) a provoqué des réponses tronquées sur plusieurs questions du jeu de test.

Prompt système anti-hallucination. Une hallucination a été détectée en production (un événement inventé de toutes pièces en réponse à une question sans résultat réel dans le périmètre demandé). Le prompt système impose une vérification explicite de tous les critères de la question (lieu, date, thème, public...) avant d'affirmer qu'un événement correspond, avec instruction de le dire clairement en l'absence de correspondance totale plutôt que de présenter un résultat partiel comme exact.

Résilience API. Le plan gratuit Mistral provoque occasionnellement des erreurs 429 (capacité insuffisante) ou 503 (instabilité). Une fonction de retry avec backoff exponentiel encadre les appels API critiques (indexation, génération de test).

Installation

Le projet utilise uv pour la gestion de l'environnement.

powershell
uv sync

Crée un fichier .env à la racine avec :

API_KEY_MISTRAL=ta_cle_api_mistral
REBUILD_TOKEN=un_token_de_ton_choix

API_KEY_MISTRAL est nécessaire pour toute génération/embedding. REBUILD_TOKEN protège l'endpoint /rebuild (voir API).

Un requirements.txt (généré via uv export --no-hashes -o requirements.txt) est également fourni pour les environnements n'utilisant pas uv.

Notes d'environnement :

Un bug de structure dans pyproject.toml (la clé dependencies rattachée par erreur à [tool.pytest.ini_options] au lieu de [project]) empêchait une installation reproductible des dépendances sur une machine tierce — corrigé.
(Windows) Un crash du kernel Jupyter lors de la construction du vectorstore FAISS a été résolu via os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" (conflit OpenMP connu entre torch et faiss-cpu).
Utilisation
En local (sans Docker)
powershell
# 1. Construire l'index vectoriel (nécessaire au premier lancement, ou après mise à jour des données)
uv run python build_index.py

# 2. Lancer l'API (terminal 1)
uv run uvicorn api.main:app --reload

# 3. Lancer l'interface Streamlit (terminal 2)
uv run streamlit run streamlit_app.py

L'API est alors disponible sur http://localhost:8000 (documentation interactive Swagger sur http://localhost:8000/docs), et l'interface Streamlit sur http://localhost:8501.

Avec Docker

L'image Docker embarque l'API et l'index vectoriel déjà construit (le rebuild de l'index se fait localement avant le build de l'image, pour ne pas nécessiter de clé API ni d'accès réseau au moment du build).

powershell
# 1. Construire l'index localement s'il n'est pas à jour
uv run python build_index.py

# 2. Construire l'image
docker build -t puls-events-api .

# 3. Lancer le conteneur
docker run -p 8000:8000 -e API_KEY_MISTRAL="ta_cle" -e REBUILD_TOKEN="ton_token" puls-events-api

L'API est ensuite accessible sur http://localhost:8000, comme en local.

API
Endpoint	Méthode	Description
/health	GET	Vérifie que l'API est opérationnelle.
/ask	POST	Prend {"question": "..."}, renvoie {"response": "..."}. 400 si la question est vide.
/rebuild	POST	Reconstruit l'index vectoriel à la demande. Protégé par le header X-Admin-Token (doit correspondre à REBUILD_TOKEN) — 422 si absent, 403 si incorrect.
/metadata	GET	Statistiques sur les données indexées : nombre d'événements, date de dernière reconstruction de l'index, villes et mots-clés disponibles.

Documentation interactive (Swagger) sur http://localhost:8000/docs, pour tester chaque endpoint directement depuis le navigateur.

Exemples d'utilisation

curl :

bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quels concerts gratuits ce week-end à Rennes ?"}'

curl http://localhost:8000/metadata

curl -X POST http://localhost:8000/rebuild \
  -H "X-Admin-Token: ton_token"

Python :

python
import requests

base_url = "http://localhost:8000"

reponse = requests.post(f"{base_url}/ask", json={"question": "Quels concerts gratuits ce week-end à Rennes ?"})
print(reponse.json()["response"])

metadata = requests.get(f"{base_url}/metadata").json()
print(f"{metadata['nb_evenements_indexes']} événements indexés dans {metadata['nb_villes']} villes")

requests.post(f"{base_url}/rebuild", headers={"X-Admin-Token": "ton_token"})
Tests
powershell
# Tous les tests unitaires (nettoyage, structuration, préparation, indexation, chaîne RAG)
uv run pytest tests/

# Tests d'intégration de l'API
uv run pytest api_test.py

tests/test_nettoyage.py, tests/test_structuration.py, tests/test_preparation.py et tests/test_indexation.py couvrent la logique pure du pipeline de données (nettoyage de texte, construction du texte/métadonnées par événement, filtrage/déduplication/fenêtre temporelle, découpage en lots et retry des appels d'embedding) — aucun n'a besoin de API_KEY_MISTRAL ni d'accès réseau. tests/test_preparation.py inclut un test xfail qui documente un bug connu de casse dans LISTE_KEYWORDS_A_EXCLURE (des mots-clés à casse mixte ne sont jamais exclus).

tests/test_generation.py vérifie que la chaîne s'exécute sans erreur, que la réponse n'est jamais vide, et qu'une question hors périmètre ne provoque pas d'hallucination (test anti-hallucination basé sur une liste de marqueurs de refus) — nécessite API_KEY_MISTRAL, sinon skip. La chaîne RAG est extraite du notebook vers src/generation.py (construire_chaine_rag) pour permettre son import direct par pytest, et l'index FAISS utilisé est chargé depuis le disque (FAISS.load_local) plutôt que reconstruit à chaque exécution, pour éviter de régénérer inutilement les embeddings.

api_test.py couvre les trois endpoints (cas valides et invalides), ainsi que la protection par token de /rebuild (le test de reconstruction complète est désactivé par défaut, activable via la variable d'environnement RUN_SLOW_TESTS).

Le dossier tests/ inclut également des tests d'intégration qui vérifient la cohérence entre data.json, l'index FAISS sur disque et les fichiers de référence générés (test_filtrage.py, test_indexation.py, test_vectorisation.py, test_data_retrieval.py, test_interrogation.py). Ces fichiers de référence (data/processed/evenements_filtres.csv, data/index/uids_attendus.json) sont des exports figés — ils se désynchronisent naturellement avec le temps qui passe (fenêtre glissante d'un an) ou après une mise à jour des données ; regenerer_references.py les recalcule à partir de l'état actuel de data.json, à relancer après chaque build_index.py.

Résultats détaillés de la dernière exécution (par fichier, avec le xfail attendu documenté) : docs/resultats-tests.md.

Évaluation

Le projet combine deux volets d'évaluation : un jeu de test annoté à la main (mesuré via relecture manuelle, similarité cosinus et Exact Match) et une évaluation automatique complémentaire via Ragas.

Jeu de test annoté

data/qa_testset.csv contient 13 questions réparties en 3 catégories :

Catégorie	Nombre	Description
factuelle_simple	5	Date, heure, lieu ou tarif d'un événement précis
multi_critere	5	Croisement de plusieurs filtres (zone géographique + thème + date, accessibilité...)
hors_perimetre	3	Réponse attendue = refus honnête (événement hors Bretagne, hors périmètre culturel, ou hors fenêtre temporelle)

Les réponses générées sont comparées aux réponses de référence dans data/qa_results.csv, selon trois méthodes complémentaires :

Évaluation manuelle : classification correcte / partielle / incorrecte, avec justification qualitative.
Similarité cosinus entre la réponse générée et la réponse de référence, via les embeddings mistral-embed.
Exact Match (chaînes normalisées : minuscules, accents et ponctuation retirés) — incluse car demandée par le brief, mais peu informative pour de la génération en texte libre où la formulation varie naturellement même quand le contenu est correct.

Résultats par catégorie :

Catégorie	Taux correcte (manuel)	Similarité moyenne
factuelle_simple	0.8 (4/5)	0.881
multi_critere	0.8 (4/5)	0.845
hors_perimetre	1.0 (3/3)	0.818

Total : 11/13 correctes, 2/13 partielles, 0/13 incorrectes — aucune hallucination détectée sur les questions hors périmètre. Exact Match : 0/13 (attendu, cf. remarque ci-dessus).

Observation notable : la catégorie hors_perimetre obtient le score de similarité le plus bas malgré le taux de correction manuelle le plus élevé (100 %). Les réponses de référence pour les refus sont volontairement courtes ("Aucune information disponible — ..."), alors que le chatbot répond de façon plus étoffée (explication, propositions d'alternatives) — correct sur le fond mais textuellement éloigné de la référence courte, ce qui abaisse la similarité cosinus sans que la réponse soit fausse. Illustre l'intérêt de combiner plusieurs métriques plutôt que de se fier à une seule.

Évaluation automatique complémentaire (Ragas)
Métrique	Score	Remarque
faithfulness	~0.65	Calculé via Ragas ; un juge Mistral (ministral-3b-2512) échoue occasionnellement à produire un JSON strictement valide sur les questions complexes, réduisant légèrement l'échantillon effectif.
context_recall	~0.77	Calculé via Ragas.
answer_relevancy	~0.86	Calcul maison (similarité cosinus entre la question posée et des questions régénérées à partir de la réponse, via mistral-embed) — la métrique ResponseRelevancy native de Ragas s'est révélée structurellement incompatible avec ChatMistralAI (erreur interne systématique, indépendante de la version de Ragas testée), documentée et contournée.
Limites connues
Un événement récurrent reste indexé tant qu'au moins une de ses occurrences est récente ou à venir (le filtre de fenêtre temporelle se base sur date_max, la date de fin de la dernière occurrence, plutôt que sur la première). En dehors de ce cas, un événement ponctuel déjà passé peut rester proposé en réponse à une question formulée au futur, jusqu'à ce qu'il sorte de la fenêtre glissante d'un an — pas de vérification stricte par rapport à la date du jour au moment de la réponse.
Formulation parfois contradictoire sur un cas précis (« Fest deizh » à Saint-M'Hervé) : la réponse affirme d'abord que l'événement n'a pas lieu à Saint-M'Hervé avant de donner une adresse à Saint-M'Hervé — faits corrects mais phrasé confus.
Le chunk le plus long du corpus (« Brest La Fest'Yves 2026 », 7531 caractères) apparaît fréquemment parmi les documents récupérés, indépendamment de la pertinence de la question — hypothèse d'une dilution de l'embedding pour un document long et hétérogène. Le LLM l'a cependant correctement écarté quand il n'était pas pertinent, sur les runs finaux.
Un cas isolé de mauvaise attribution géographique a été observé sur un run antérieur (Bain-de-Bretagne attribué aux Côtes-d'Armor au lieu de l'Ille-et-Vilaine), non reproduit sur le run final.
La métrique ResponseRelevancy de Ragas est incompatible avec ChatMistralAI (voir Évaluation) — contournée par un calcul maison.
langchain-community (utilisé pour FAISS) est annoncé en dépréciation par LangChain — migration future à prévoir.
Structure du projet
├── api/
│   └── main.py              # API FastAPI (/health, /ask, /rebuild)
├── src/
│   ├── preparation.py       # Nettoyage et filtrage des données Open Agenda
│   ├── indexation.py        # Construction de l'index FAISS
│   ├── generation.py        # Chaîne RAG (LCEL), prompt système
│   └── nettoyage.py         # Fonctions de nettoyage de texte
├── tests/
│   ├── test_generation.py    # Tests unitaires de la chaîne RAG
│   ├── test_nettoyage.py     # Tests du nettoyage de texte
│   ├── test_structuration.py # Tests de construction texte/métadonnées
│   ├── test_preparation.py   # Tests du pipeline de préparation des données
│   └── test_indexation.py    # Tests du découpage en lots et du retry d'embedding
├── data/
│   ├── data.json             # Données brutes Open Agenda
│   ├── qa_testset.csv        # Jeu de test annoté (13 questions)
│   ├── qa_results.csv        # Réponses générées + réponses de référence
│   ├── processed/evenements_filtres.csv  # Export du DataFrame filtré (généré)
│   └── index/
│       ├── faiss_vectorstore    # Index vectoriel FAISS (généré)
│       └── uids_attendus.json   # Référence des événements attendus dans l'index (généré)
├── notebooks/notebook.ipynb  # Exploration et développement du pipeline
├── build_index.py           # Script de build de l'index vectoriel
├── regenerer_references.py  # Régénère evenements_filtres.csv et uids_attendus.json
├── evaluate_rag.py          # Évaluation automatique (Ragas + calcul maison)
├── api_test.py               # Tests d'intégration de l'API
├── streamlit_app.py          # Interface Streamlit
├── Dockerfile
├── .dockerignore
├── pyproject.toml / uv.lock  # Dépendances (gérées avec uv)
└── requirements.txt          # Export des dépendances (compatibilité pip)
Pistes d'amélioration
Migrer vers l'API non dépréciée de Ragas (ragas.metrics.collections) une fois la compatibilité Mistral corrigée en amont.
Prendre en compte la date courante pour filtrer les événements déjà passés.
Ajouter des filtres structurés (date, ville, thème) en complément de la recherche sémantique.
Explorer un chunking plus fin pour les événements très longs, pour limiter l'effet de dilution observé sur l'embedding.