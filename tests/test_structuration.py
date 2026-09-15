from src.structuration import valeur_ou_defaut, formater_dates, extraire_contacts, formater_inscription


def test_valeur_ou_defaut_none():
    assert valeur_ou_defaut(None, "défaut") == "défaut"


def test_valeur_ou_defaut_nan():
    assert valeur_ou_defaut(float("nan"), "défaut") == "défaut"


def test_valeur_ou_defaut_chaine_vide_ou_espaces():
    assert valeur_ou_defaut("", "défaut") == "défaut"
    assert valeur_ou_defaut("   ", "défaut") == "défaut"


def test_valeur_ou_defaut_valeur_valide_conservee():
    assert valeur_ou_defaut("Paris", "défaut") == "Paris"
    assert valeur_ou_defaut(5, "défaut") == 5


def test_formater_dates_occurrence_unique():
    dates = [("2026-04-19T15:00:00+02:00", "2026-04-19T18:00:00+02:00")]
    resultat = formater_dates(dates, dates[0][0], dates[0][0], 1)
    assert resultat == "le 2026-04-19"


def test_formater_dates_peu_occurrences():
    dates = [
        ("2026-04-19T15:00:00+02:00", "x"),
        ("2026-04-20T15:00:00+02:00", "x"),
        ("2026-04-21T15:00:00+02:00", "x"),
    ]
    resultat = formater_dates(dates, dates[0][0], dates[-1][0], 3)
    assert resultat == "les 2026-04-19, 2026-04-20, 2026-04-21"


def test_formater_dates_beaucoup_occurrences():
    dates = [(f"2026-04-{19 + i:02d}T15:00:00+02:00", "x") for i in range(6)]
    resultat = formater_dates(dates, dates[0][0], dates[-1][0], 6)
    assert resultat == "du 2026-04-19 au 2026-04-24 (6 dates)"


def test_extraire_contacts_cas_normal():
    registration = [
        {"type": "phone", "value": "0102030405"},
        {"type": "email", "value": "contact@example.com"},
        {"type": "link", "value": "https://example.com"},
    ]
    assert extraire_contacts(registration) == {
        "telephones": ["0102030405"],
        "emails": ["contact@example.com"],
        "liens": ["https://example.com"],
    }


def test_extraire_contacts_valeur_non_liste():
    assert extraire_contacts(None) == {"telephones": [], "emails": [], "liens": []}
    assert extraire_contacts(float("nan")) == {"telephones": [], "emails": [], "liens": []}


def test_extraire_contacts_liste_vide():
    assert extraire_contacts([]) == {"telephones": [], "emails": [], "liens": []}


def test_formater_inscription_telephone_et_email():
    contacts = {"telephones": ["0102030405"], "emails": ["contact@example.com"], "liens": []}
    assert formater_inscription(contacts) == " Inscription : téléphone : 0102030405 ; email : contact@example.com."


def test_formater_inscription_telephone_seul():
    contacts = {"telephones": ["0102030405"], "emails": [], "liens": []}
    assert formater_inscription(contacts) == " Inscription : téléphone : 0102030405."


def test_formater_inscription_rien_de_disponible():
    contacts = {"telephones": [], "emails": [], "liens": []}
    assert formater_inscription(contacts) == ""

from src.structuration import construire_texte, construire_metadata


def test_construire_texte_cas_complet():
    row = {
        "location_name": "La Cale",
        "location_city": "Rennes",
        "location_address": "12 rue de la Mer",
        "dates": [("2026-04-19T15:00:00+02:00", "2026-04-19T18:00:00+02:00")],
        "date_min": "2026-04-19T15:00:00+02:00",
        "date_max": "2026-04-19T15:00:00+02:00",
        "nb_occurrences": 1,
        "keywords_fr": ["Exposition", "Peinture"],
        "accessibility_label_fr": "Accès PMR",
        "age_min": 6,
        "age_max": 12,
        "registration": [
            {"type": "phone", "value": "0102030405"},
            {"type": "email", "value": "contact@example.com"},
        ],
        "title_fr": "Aux Abords de la Ville",
        "texte_description": "Une exposition de peinture locale.",
        "conditions_fr": "Gratuit sur réservation",
    }

    resultat = construire_texte(row)

    assert resultat == (
        "Aux Abords de la Ville. Une exposition de peinture locale."
        " Catégories : Exposition, Peinture."
        " Lieu : La Cale, 12 rue de la Mer. Dates : le 2026-04-19."
        " Conditions : Gratuit sur réservation."
        " Accessibilité : Accès PMR. Âge : de 6 à 12 ans."
        " Inscription : téléphone : 0102030405 ; email : contact@example.com."
    )


def test_construire_texte_champs_optionnels_absents():
    row = {
        "location_name": None,
        "location_city": "Rennes",
        "location_address": "",
        "dates": [("2026-04-19T15:00:00+02:00", "2026-04-19T18:00:00+02:00")],
        "date_min": "2026-04-19T15:00:00+02:00",
        "date_max": "2026-04-19T15:00:00+02:00",
        "nb_occurrences": 1,
        "keywords_fr": [],
        "accessibility_label_fr": None,
        "age_min": None,
        "age_max": None,
        "registration": None,
        "title_fr": "Concert",
        "texte_description": "Un concert.",
        "conditions_fr": "",
    }

    resultat = construire_texte(row)

    assert resultat == (
        "Concert. Un concert."
        " Lieu : Rennes. Dates : le 2026-04-19."
        " Accessibilité : Pas de précision. Âge : non précisé."
    )


def test_construire_texte_age_min_seul():
    row = {
        "location_name": "Salle A",
        "location_city": "Brest",
        "location_address": "",
        "dates": [("2026-05-01T10:00:00+02:00", "2026-05-01T12:00:00+02:00")],
        "date_min": "2026-05-01T10:00:00+02:00",
        "date_max": "2026-05-01T10:00:00+02:00",
        "nb_occurrences": 1,
        "keywords_fr": [],
        "accessibility_label_fr": None,
        "age_min": 8,
        "age_max": None,
        "registration": None,
        "title_fr": "Atelier",
        "texte_description": "Un atelier.",
        "conditions_fr": "",
    }

    resultat = construire_texte(row)
    assert "Âge : à partir de 8 ans." in resultat


def test_construire_metadata_cas_complet():
    row = {
        "uids": [12345],
        "title_fr": "Aux Abords de la Ville",
        "location_city": "Rennes",
        "location_district": "Centre",
        "location_postalcode": "35000",
        "location_department": "Ille-et-Vilaine",
        "dates": [("2026-04-19T15:00:00+02:00", "2026-04-19T18:00:00+02:00")],
        "date_min": "2026-04-19T15:00:00+02:00",
        "date_max": "2026-04-19T15:00:00+02:00",
        "keywords_fr": ["Exposition"],
        "canonicalurl": "https://openagenda.com/events/aux-abords",
        "registration": [{"type": "phone", "value": "0102030405"}],
    }

    resultat = construire_metadata(row)

    assert resultat == {
        "uids": [12345],
        "titre": "Aux Abords de la Ville",
        "ville": "Rennes",
        "quartier": "Centre",
        "code_postal": "35000",
        "departement": "Ille-et-Vilaine",
        "dates": [("2026-04-19T15:00:00+02:00", "2026-04-19T18:00:00+02:00")],
        "date_min": "2026-04-19T15:00:00+02:00",
        "date_max": "2026-04-19T15:00:00+02:00",
        "mots_cles": ["Exposition"],
        "url": "https://openagenda.com/events/aux-abords",
        "telephones": ["0102030405"],
        "emails": [],
        "liens": [],
    }


def test_construire_metadata_champs_optionnels_absents():
    row = {
        "uids": [999],
        "title_fr": "Concert",
        "location_city": "Brest",
        "dates": [("2026-05-01T10:00:00+02:00", "2026-05-01T12:00:00+02:00")],
        "date_min": "2026-05-01T10:00:00+02:00",
        "date_max": "2026-05-01T10:00:00+02:00",
        "keywords_fr": None,
        "canonicalurl": "https://openagenda.com/events/concert",
        "registration": None,
    }

    resultat = construire_metadata(row)

    assert resultat["quartier"] is None
    assert resultat["code_postal"] is None
    assert resultat["departement"] is None
    assert resultat["mots_cles"] == []
    assert resultat["telephones"] == []