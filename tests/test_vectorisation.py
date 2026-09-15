import numpy as np


def test_dimension_vecteurs(vectorstore):
    vecteurs = vectorstore.index.reconstruct_n(0, vectorstore.index.ntotal)
    # 1024 = dimension connue de mistral-embed ; ajuste si ta valeur diffère
    assert vecteurs.shape == (vectorstore.index.ntotal, 1024)


def test_pas_de_valeurs_invalides(vectorstore):
    vecteurs = vectorstore.index.reconstruct_n(0, vectorstore.index.ntotal)
    assert not np.isnan(vecteurs).any()
    assert not np.isinf(vecteurs).any()


def test_pas_de_vecteurs_nuls(vectorstore):
    vecteurs = vectorstore.index.reconstruct_n(0, vectorstore.index.ntotal)
    normes = np.linalg.norm(vecteurs, axis=1)
    assert (normes > 0).all()