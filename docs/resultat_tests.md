Résultats des tests unitaires et d'intégration

Dernière exécution : uv run pytest tests/ (voir la commande exacte dans le README).

collected 54 items

tests\test_data_retrieval.py ...                                          [  5%]
tests\test_filtrage.py ..                                                 [  9%]
tests\test_generation.py ...                                              [ 14%]
tests\test_indexation.py ..                                               [ 18%]
tests\test_interrogation.py .                                             [ 20%]
tests\test_nettoyage.py ........                                          [ 35%]
tests\test_preparation.py ...........x..                                  [ 61%]
tests\test_structuration.py ..................                            [ 94%]
tests\test_vectorisation.py ...                                           [100%]

53 passed, 1 xfailed in 14.29s
Résumé par fichier
Fichier	Ce qu'il couvre	Résultat
test_nettoyage.py	Nettoyage HTML/espaces (src/nettoyage.py)	8/8 passed
test_structuration.py	Construction du texte et des métadonnées par événement (src/structuration.py)	18/18 passed
test_preparation.py	Filtrage, déduplication, fenêtre temporelle, exclusion par mots-clés (src/preparation.py)	14 passed, 1 xfailed
test_indexation.py	Découpage en lots, retry d'embedding, et cohérence taille index ↔ documents indexés	2/2 passed
test_filtrage.py	Cohérence de data/processed/evenements_filtres.csv (fenêtre d'un an)	2/2 passed
test_data_retrieval.py	Récupération des données sources	3/3 passed
test_vectorisation.py	Vectorisation des documents	3/3 passed
test_interrogation.py	Interrogation de l'index vectoriel	1/1 passed
test_generation.py	Exécution de la chaîne RAG, réponse non vide, anti-hallucination (nécessite API_KEY_MISTRAL)	3/3 passed

api_test.py (tests d'intégration de l'API, exécutés séparément via uv run pytest api_test.py) couvre les endpoints /health, /ask et /rebuild, cas valides et invalides inclus.

Le xfail attendu

test_preparation.py::TestExclusionMotsCles::test_mot_cle_a_casse_mixte_ne_matche_jamais_bug_connu est marqué xfail(strict=True) : il documente un bug connu de casse dans LISTE_KEYWORDS_A_EXCLURE (certaines entrées à casse mixte, comme "Aides à l'emploi", ne sont jamais exclues car comparées via k.lower()). Ce test doit rester en échec attendu tant que le bug n'est pas corrigé — s'il se met à passer (XPASS), c'est le signal qu'il faut retirer le marqueur.

Erreurs fréquentes / limites identifiées via les tests
Un événement récurrent pouvait être totalement exclu de l'index à cause de sa toute première occurrence historique (corrigé : le filtre de fenêtre temporelle utilise désormais date_max, la date de fin de la dernière occurrence — voir Limites connues).
data/processed/evenements_filtres.csv et data/index/uids_attendus.json sont des exports figés qui se désynchronisent naturellement avec le temps (fenêtre glissante) ou après une mise à jour des données — regenerer_references.py les recalcule à partir de l'état actuel de data.json.
Le bug de casse dans LISTE_KEYWORDS_A_EXCLURE (voir ci-dessus).
Indicateurs de qualité (jeu de test annoté)

Voir la section Évaluation du README pour les indicateurs sur la qualité des réponses générées (taux de réponse correcte par catégorie, similarité cosinus, faithfulness/context_recall via Ragas) — ces indicateurs mesurent la qualité du système, distincts des tests unitaires ci-dessus qui valident le code.