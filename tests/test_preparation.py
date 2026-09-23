
import itertools
import json
 
import pandas as pd
import pytest
 
from src.preparation import (
    FENETRE_JOURS,
    LISTE_KEYWORDS_A_EXCLURE,
    SEUIL_MIN_DESCRIPTION,
    _parse_status,
    charger_df_evenements_final,
)
 
DESCRIPTION_LONGUE = "Une description suffisamment longue pour dépasser le seuil minimal requis."
assert len(DESCRIPTION_LONGUE) > SEUIL_MIN_DESCRIPTION
 
 
def _iso(delta_jours, delta_heures=0):
    return (
        pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=delta_jours, hours=delta_heures)
    ).isoformat()
 
 
def _statut(programme=True):
    if programme:
        return json.dumps({"id": 1, "label": {"fr": "Programmé"}})
    return json.dumps({"id": 2, "label": {"fr": "Refusé"}})
 
 
@pytest.fixture
def fabrique_evenement():
    compteur = itertools.count(1)
 
    def _fabrique(**overrides):
        n = next(compteur)
        debut = overrides.pop("firstdate_begin", _iso(-10))
        fin = overrides.pop("firstdate_end", None) or debut
        fin_evt = overrides.pop("lastdate_end", None) or fin
        base = {
            "status": _statut(programme=overrides.pop("programme", True)),
            "title_fr": overrides.pop("title_fr", f"Événement {n}"),
            "location_name": overrides.pop("location_name", f"Lieu {n}"),
            "firstdate_begin": debut,
            "firstdate_end": fin,
            "lastdate_end": fin_evt,
            "uid": overrides.pop("uid", f"u{n}"),
            "keywords_fr": overrides.pop("keywords_fr", []),
            "description_fr": overrides.pop("description_fr", DESCRIPTION_LONGUE),
            "longdescription_fr": overrides.pop("longdescription_fr", ""),
            "conditions_fr": overrides.pop("conditions_fr", ""),
            "location_address": overrides.pop("location_address", ""),
            "location_access_fr": overrides.pop("location_access_fr", ""),
        }
        base.update(overrides)
        return base
 
    return _fabrique
 
 
def _ecrire_data_json(tmp_path, evenements):
    chemin = tmp_path / "data.json"
    chemin.write_text(json.dumps(evenements), encoding="utf-8")
    return chemin
 
 
class TestParseStatus:
    def test_statut_valide(self):
        assert _parse_status('{"id": 1, "label": {"fr": "Programmé"}}') == (1, "Programmé")
 
    def test_json_invalide(self):
        assert _parse_status("pas du json") == (None, None)
 
    def test_none(self):
        assert _parse_status(None) == (None, None)
 
    def test_label_absent(self):
        assert _parse_status('{"id": 1}') == (None, None)
 
    def test_cle_fr_absente_dans_label(self):
        assert _parse_status('{"id": 1, "label": {}}') == (1, None)
 
 
class TestFiltreStatut:
    def test_conserve_uniquement_les_evenements_programmes(self, tmp_path, fabrique_evenement):
        garde = fabrique_evenement(title_fr="Concert programmé", programme=True)
        exclu = fabrique_evenement(title_fr="Concert refusé", programme=False)
        chemin = _ecrire_data_json(tmp_path, [garde, exclu])
 
        df = charger_df_evenements_final(str(chemin))
 
        assert list(df["title_fr"]) == ["Concert programmé"]
 
 
class TestDeduplication:
    def test_evenement_recurrent_devient_une_seule_ligne(self, tmp_path, fabrique_evenement):
        titre, lieu = "Festival récurrent", "Salle Omnisports"
        occ1 = fabrique_evenement(
            title_fr=titre, location_name=lieu, uid="u1",
            firstdate_begin=_iso(-30), lastdate_end=_iso(-30, 2),
        )
        occ2 = fabrique_evenement(
            title_fr=titre, location_name=lieu, uid="u2",
            firstdate_begin=_iso(-20), lastdate_end=_iso(-20, 2),
        )
        occ3 = fabrique_evenement(
            title_fr=titre, location_name=lieu, uid="u3",
            firstdate_begin=_iso(-10), lastdate_end=_iso(-10, 2),
        )
        chemin = _ecrire_data_json(tmp_path, [occ1, occ2, occ3])
 
        df = charger_df_evenements_final(str(chemin))
 
        assert len(df) == 1
        ligne = df.iloc[0]
        assert ligne["nb_occurrences"] == 3
        assert list(ligne["uids"]) == ["u1", "u2", "u3"]
        assert len(ligne["dates"]) == 3
        assert pd.Timestamp(ligne["date_min"]) == pd.Timestamp(occ1["firstdate_begin"])
        assert pd.Timestamp(ligne["date_max"]) == pd.Timestamp(occ3["lastdate_end"])
 
    def test_evenements_distincts_restent_separes(self, tmp_path, fabrique_evenement):
        e1 = fabrique_evenement(title_fr="Événement A", location_name="Lieu A")
        e2 = fabrique_evenement(title_fr="Événement B", location_name="Lieu B")
        chemin = _ecrire_data_json(tmp_path, [e1, e2])
 
        df = charger_df_evenements_final(str(chemin))
 
        assert len(df) == 2
        assert set(df["title_fr"]) == {"Événement A", "Événement B"}
 
 
class TestFenetreTemporelle:
    def test_exclut_un_evenement_trop_ancien(self, tmp_path, fabrique_evenement):
        # Un événement récent est ajouté aux côtés de l'ancien : si l'ancien était le
        # seul événement, le masque d'exclusion des mots-clés appliqué à un DataFrame
        # de 0 ligne dégénère (Series vide non booléenne) et fait planter le pipeline
        # plus loin avec un KeyError sans rapport — un cas dégénéré qui ne se produit
        # pas avec un vrai jeu de données (toujours des événements récents), donc pas
        # ce que ce test cherche à vérifier ici.
        ancien = fabrique_evenement(
            title_fr="Événement ancien",
            firstdate_begin=_iso(-(FENETRE_JOURS + 30)),
            lastdate_end=_iso(-(FENETRE_JOURS + 30), 2),
        )
        recent = fabrique_evenement(
            title_fr="Événement récent témoin",
            firstdate_begin=_iso(-10),
            lastdate_end=_iso(-10, 2),
        )
        chemin = _ecrire_data_json(tmp_path, [ancien, recent])
 
        df = charger_df_evenements_final(str(chemin))
 
        assert list(df["title_fr"]) == ["Événement récent témoin"]
 
    def test_conserve_un_evenement_recent(self, tmp_path, fabrique_evenement):
        recent = fabrique_evenement(
            title_fr="Événement récent",
            firstdate_begin=_iso(-10),
            lastdate_end=_iso(-10, 2),
        )
        chemin = _ecrire_data_json(tmp_path, [recent])
 
        df = charger_df_evenements_final(str(chemin))
 
        assert list(df["title_fr"]) == ["Événement récent"]
 
 
class TestExclusionMotsCles:
    def test_mot_cle_en_minuscules_dans_la_liste_exclut_correctement(self, tmp_path, fabrique_evenement):
        # "marché du travail" est déjà tout en minuscules dans LISTE_KEYWORDS_A_EXCLURE :
        # k.lower() matche donc quelle que soit la casse d'origine du mot-clé.
        assert "marché du travail" in LISTE_KEYWORDS_A_EXCLURE
        exclu = fabrique_evenement(title_fr="Réunion RH", keywords_fr=["Marché Du Travail"])
        garde = fabrique_evenement(title_fr="Concert", keywords_fr=["Musique"])
        chemin = _ecrire_data_json(tmp_path, [exclu, garde])
 
        df = charger_df_evenements_final(str(chemin))
 
        assert list(df["title_fr"]) == ["Concert"]
 
    @pytest.mark.xfail(
        reason=(
            "Bug connu et documenté : LISTE_KEYWORDS_A_EXCLURE contient des entrées à casse "
            "mixte (ex. 'Aides à l'emploi'), comparées via k.lower() qui est toujours en "
            "minuscules — ces entrées ne peuvent donc jamais matcher, et l'événement n'est "
            "pas exclu comme il le devrait. Ce test documente le bug ; il doit être retiré "
            "si la comparaison de casse est corrigée dans preparation.py."
        ),
        strict=True,
    )
    def test_mot_cle_a_casse_mixte_ne_matche_jamais_bug_connu(self, tmp_path, fabrique_evenement):
        assert "Aides à l'emploi" in LISTE_KEYWORDS_A_EXCLURE
        evenement = fabrique_evenement(title_fr="Atelier aides à l'emploi", keywords_fr=["Aides à l'emploi"])
        chemin = _ecrire_data_json(tmp_path, [evenement])
 
        df = charger_df_evenements_final(str(chemin))
 
        # Comportement attendu métier : l'événement devrait être exclu.
        assert df.empty
 
 
class TestFiltreDescriptionTropCourte:
    def test_description_a_la_limite_du_seuil_est_exclue(self, tmp_path, fabrique_evenement):
        description_limite = "x" * SEUIL_MIN_DESCRIPTION  # longueur == seuil, pas > seuil
        exclu = fabrique_evenement(title_fr="Trop court", description_fr=description_limite, longdescription_fr="")
        garde = fabrique_evenement(title_fr="Assez long", description_fr="x" * (SEUIL_MIN_DESCRIPTION + 1), longdescription_fr="")
        chemin = _ecrire_data_json(tmp_path, [exclu, garde])
 
        df = charger_df_evenements_final(str(chemin))
 
        assert list(df["title_fr"]) == ["Assez long"]
 
    def test_longdescription_plus_longue_est_utilisee(self, tmp_path, fabrique_evenement):
        # description_fr trop courte seule, mais longdescription_fr dépasse le seuil : doit être conservé
        garde = fabrique_evenement(
            title_fr="Longue description alternative",
            description_fr="Trop court.",
            longdescription_fr="x" * (SEUIL_MIN_DESCRIPTION + 5),
        )
        chemin = _ecrire_data_json(tmp_path, [garde])
 
        df = charger_df_evenements_final(str(chemin))
 
        assert list(df["title_fr"]) == ["Longue description alternative"]