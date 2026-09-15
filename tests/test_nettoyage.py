from src.nettoyage import nettoyer_html, normaliser_espaces, nettoyer_texte


def test_nettoyer_html_supprime_les_balises():
    texte = "<p>Bonjour <strong>le monde</strong></p>"
    resultat = nettoyer_html(texte)
    assert "<" not in resultat and ">" not in resultat
    assert "Bonjour" in resultat and "le monde" in resultat


def test_nettoyer_html_decode_les_entites():
    texte = "<p>Caf&eacute; &amp; croissant</p>"
    resultat = nettoyer_html(texte)
    assert "Café & croissant" in resultat


def test_nettoyer_html_gere_les_valeurs_vides_ou_non_textuelles():
    assert nettoyer_html("") == ""
    assert nettoyer_html(None) == ""
    assert nettoyer_html("   ") == ""


def test_normaliser_espaces_reduit_espaces_multiples():
    assert normaliser_espaces("Bonjour     le monde") == "Bonjour le monde"


def test_normaliser_espaces_supprime_espace_insecable():
    assert "\xa0" not in normaliser_espaces("10\xa0h\xa000")


def test_normaliser_espaces_supprime_caracteres_invisibles():
    resultat = normaliser_espaces("Bonjour\u200b le monde\ufeff")
    assert "\u200b" not in resultat and "\ufeff" not in resultat


def test_normaliser_espaces_strip_les_bords():
    assert normaliser_espaces("   Bonjour   ") == "Bonjour"


def test_nettoyer_texte_bout_en_bout():
    texte = "<p>Bonjour&nbsp;&nbsp;le    monde</p>"
    assert nettoyer_texte(texte) == "Bonjour le monde"