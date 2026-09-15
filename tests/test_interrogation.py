import random


def test_taux_auto_retrouvaille(vectorstore, chunks_indexes):
    random.seed(42)  # reproductibilité d'un run à l'autre
    echantillon = random.sample(chunks_indexes, k=20)

    reussites = 0
    for chunk in echantillon:
        titre = chunk.metadata["titre"]
        resultats = vectorstore.similarity_search(titre, k=5)
        uids_trouves = {
            tuple(r.metadata["uids"]) if isinstance(r.metadata["uids"], list) else r.metadata["uids"]
            for r in resultats
        }
        uid_source = (
            tuple(chunk.metadata["uids"]) if isinstance(chunk.metadata["uids"], list) else chunk.metadata["uids"]
        )
        if uid_source in uids_trouves:
            reussites += 1

    taux = reussites / len(echantillon)
    print(f"\nTaux d'auto-retrouvaille : {taux:.0%} ({reussites}/{len(echantillon)})")
    assert taux >= 0.8, f"Taux d'auto-retrouvaille trop faible : {taux:.0%}"