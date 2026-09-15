def test_index_taille_coherente(vectorstore, chunks_indexes):
    assert vectorstore.index.ntotal == len(chunks_indexes)

def test_tous_evenements_representes(chunks_indexes, uids_attendus):
    def normaliser(uids):
        return tuple(uids) if isinstance(uids, list) else uids

    uids_attendus_norm = {normaliser(u) for u in uids_attendus}
    uids_indexes = {normaliser(chunk.metadata["uids"]) for chunk in chunks_indexes}

    manquants = uids_attendus_norm - uids_indexes
    assert not manquants, f"{len(manquants)} événement(s) absents de l'index : {manquants}"