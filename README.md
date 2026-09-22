Synthèse Étape 4 — Chatbot RAG (Puls-Events)

Document de travail à reformuler dans le README.md / rapport technique. Compile les décisions techniques et résultats établis au fil du développement de l'étape 4.

1. Pipeline de données et chunking
Corpus : 1651 événements culturels en Bretagne, issus d'Open Agenda, structurés en documents LangChain (texte_embedding + metadata).
Choix de chunking : 1 chunk = 1 événement entier, aucun découpage supplémentaire.
Un premier essai avec RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100) fragmentait 916 des 1651 événements (>55%) en un chunk principal (titre + description + lieu) et un chunk résiduel de ~120-140 caractères ne contenant que des métadonnées pratiques (dates, conditions, accessibilité, âge), sans aucune information d'identification de l'événement.
Conséquence observée : le chatbot répondait parfois "titre non précisé" sur des événements dont seul le chunk résiduel avait été récupéré par similarité.
Correction : suppression du découpage, chaque événement devient un unique Document. Validé comme sûr car la longueur maximale d'un événement (7531 caractères) reste bien en-deçà de la fenêtre de contexte de mistral-embed.
Statistiques du corpus après correction (sur texte_embedding) : min 227, max 7531, moyenne 1054.7 caractères ; 110 événements > 2000 caractères, 9 événements > 4000 caractères.
2. Retriever
k = 3, déterminé par la méthode du coude (graphique en coude) plutôt que fixé arbitrairement.
3. Modèle de génération
ministral-3b-2512 retenu pour la génération.
Justification : mistral-small-latest et mistral-medium-latest renvoyaient systématiquement des erreurs 429 (rate limit), incompatibles avec le plan gratuit Mistral utilisé pour le projet. ministral-3b-2512 fonctionne de façon stable.
max_tokens du LLM augmenté (à ajuster/confirmer la valeur finale) après que le passage à des chunks plus longs (suite à la correction du chunking) a provoqué des réponses tronquées en sortie de génération sur plusieurs questions du jeu de test.
4. Jeu de test annoté (data/qa_testset.csv)

13 questions réparties en 3 catégories :

5 questions factuelle_simple (date, heure, lieu, tarif d'un événement précis)
5 questions multi_critere (croisement de plusieurs filtres : zone géographique + thème + date, accessibilité, etc.)
3 questions hors_perimetre (réponse attendue = refus honnête : événement hors Bretagne, hors périmètre culturel, ou hors fenêtre temporelle de la base)
5. Méthodologie d'évaluation

Deux approches complémentaires appliquées sur data/qa_results.csv :

Évaluation manuelle : classification correcte / partielle / incorrecte + justification qualitative, question par question.
Métriques automatiques :
Score de similarité cosinus entre la réponse générée et la réponse de référence, via embeddings mistral-embed.
Exact Match (comparaison de chaînes normalisées : minuscules, accents et ponctuation retirés) — incluse car demandée par le brief, mais peu informative pour de la génération en texte libre où la formulation varie naturellement même quand le contenu est correct.
6. Résultats

Évaluation manuelle (taux de réponses "correcte" par catégorie) :

Catégorie	Taux correcte
factuelle_simple	0.8 (4/5)
multi_critere	0.8 (4/5)
hors_perimetre	1.0 (3/3)

Total : 11/13 correcte, 2/13 partielle, 0/13 incorrecte. Aucune hallucination détectée sur les questions hors périmètre.

Score de similarité moyen par catégorie :

Catégorie	Similarité moyenne
factuelle_simple	0.881
multi_critere	0.845
hors_perimetre	0.818

Exact Match : 0/13 (attendu — confirme la limite de cette métrique pour de la génération en texte libre, cf. section méthodologie).

Observation notable : la catégorie hors_perimetre a le score de similarité le plus bas malgré le taux de correction manuelle le plus élevé (100%). Explication : les réponses de référence pour les refus sont volontairement courtes ("Aucune information disponible — ..."), alors que le chatbot répond de façon plus étoffée (explications, propositions d'alternatives) — correct sur le fond mais textuellement éloigné de la référence courte, ce qui abaisse la similarité cosinus sans que la réponse soit fausse. Illustre l'intérêt de combiner plusieurs métriques plutôt que de se fier à une seule.

7. Tests unitaires (bloc génération)
Chaîne RAG extraite du notebook vers src/generation.py (fonction construire_chaine_rag), pour permettre l'import par pytest indépendamment de Jupyter.
Index FAISS persisté sur disque (FAISS.save_local / load_local) plutôt que reconstruit à chaque test (évite de re-générer les embeddings à chaque run).
tests/test_generation.py — 3 tests :
la chaîne s'exécute sans lever d'exception sur une question valide ;
la réponse générée n'est jamais vide ;
test anti-hallucination : sur une question hors périmètre, la réponse doit indiquer une absence d'information plutôt qu'inventer un événement (vérifié via une liste de marqueurs de refus).
Tests conditionnés à la présence de API_KEY_MISTRAL (skip sinon, pour un environnement CI sans secret).
8. Limites observées
Formulation parfois contradictoire sur un cas précis (Fest deizh de Saint-M'Hervé) : la réponse affirme d'abord que l'événement n'a pas lieu à Saint-M'Hervé avant de donner une adresse à Saint-M'Hervé — faits corrects mais phrasé confus.
Le chunk le plus long du corpus ("Brest La Fest'Yves 2026", 7531 caractères) apparaissait fréquemment parmi les documents récupérés, indépendamment de la pertinence de la question — hypothèse d'une "dilution" de l'embedding pour un document long et hétérogène. Le LLM a cependant correctement écarté ce chunk quand il n'était pas pertinent, dans les runs finaux.
Un cas isolé de mauvaise attribution géographique observé sur un run antérieur (Bain-de-Bretagne attribué aux Côtes-d'Armor au lieu de l'Ille-et-Vilaine), non reproduit sur le run final.
Absence de prise en compte explicite de la date courante : des événements déjà passés peuvent être proposés en réponse à une question formulée au futur ("prévu").
langchain-community (utilisé pour FAISS) est annoncé en dépréciation par LangChain — migration future à prévoir vers un package d'intégration autonome.
9. Environnement / configuration
Gestion de l'environnement via uv (pyproject.toml + uv.lock).
Correction d'un bug de structure TOML où dependencies était mal rattaché à [tool.pytest.ini_options] au lieu de [project] — cassait l'installation reproductible des dépendances sur une machine tierce.
(Windows) Un crash du kernel Jupyter lors de la construction du vectorstore FAISS a été résolu via os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" (conflit connu OpenMP entre torch et faiss-cpu).