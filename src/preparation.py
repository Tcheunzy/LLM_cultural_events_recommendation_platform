"""
Préparation des données événements : du fichier brut Open Agenda (data.json)
à df_evenements_final, tel qu'utilisé pour construire les embeddings.

Extrait des cellules de nettoyage/exploration du notebook, pour être
réutilisable depuis l'API (endpoint /rebuild) sans dépendre de Jupyter.
"""

import json
from pathlib import Path

import pandas as pd

from src.nettoyage import nettoyer_texte

LISTE_COLONNES_A_SUPPRIMER = [
    "contributor_organization", "category", "contributor_contactposition",
    "contributor_contactname", "contributor_contactnumber", "contributor_email",
    "links", "location_insee", "location_countrycode", "location_imagecredits",
    "location_image", "originalimage", "thumbnail", "imagecredits", "image",
    "_occurrence",
]

LISTE_KEYWORDS_A_EXCLURE = [
    "détection de potentiel", "marché du travail", "s'informer",
    "découverte secteur / métier", "opportunité d'emploi",
    "1 jeune  1 solution", "se préparer", "Aides à l'emploi",
    "Création d'entreprise", "Emploi/emploi", "Insertion, entreprise",
    "entreprises", "outil métier",
]

COLONNES_TEXTE = [
    "title_fr", "description_fr", "longdescription_fr", "conditions_fr",
    "location_name", "location_address", "location_access_fr",
]

SEUIL_MIN_DESCRIPTION = 36
FENETRE_JOURS = 365


def _parse_status(s):
    try:
        d = json.loads(s)
        return d["id"], d["label"].get("fr")
    except (TypeError, ValueError, KeyError):
        return None, None


def charger_df_evenements_final(chemin_data: str = "data/data.json") -> pd.DataFrame:
    """Reproduit le pipeline de nettoyage du notebook, de data.json à df_evenements_final."""

    df = pd.read_json(Path(chemin_data))

    # Statut : ne garder que les événements réellement programmés (status_id == 1)
    df[["status_id", "status_label"]] = df["status"].apply(lambda s: pd.Series(_parse_status(s)))
    df = df[df["status_id"] == 1].copy()
    assert df["status_id"].eq(1).all()

    # Déduplication : un événement répété sur plusieurs dates devient une seule ligne,
    # avec la liste de ses dates conservée (uids, dates)
    df["_occurrence"] = list(zip(df["firstdate_begin"], df["firstdate_end"]))
    agg_dates = (
        df.groupby(["title_fr", "location_name"])
          .agg(
              uids=("uid", list),
              dates=("_occurrence", lambda s: sorted(set(s))),
              date_min=("firstdate_begin", "min"),
              date_max=("lastdate_end", "max"),
              nb_occurrences=("uid", "count"),
          )
    )
    representative = df.sort_values("firstdate_begin").groupby(["title_fr", "location_name"]).first()
    df_evenements_clean = (
        representative.join(agg_dates[["uids", "dates", "date_min", "date_max", "nb_occurrences"]])
                      .reset_index()
                      .drop(columns=LISTE_COLONNES_A_SUPPRIMER, errors="ignore")
    )

    # Fenêtre temporelle : événements dont la date de fin est dans la dernière année ou à venir
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=FENETRE_JOURS)
    dates_fin_utc = pd.to_datetime(df_evenements_clean["date_max"], utc=True)
    df_evenements_clean = df_evenements_clean[dates_fin_utc >= cutoff].copy()

    # Exclusion des événements hors périmètre culturel (via mots-clés)
    mask_a_exclure = df_evenements_clean["keywords_fr"].apply(
        lambda kws: any(k.lower() in LISTE_KEYWORDS_A_EXCLURE for k in kws)
    )
    df_evenements_final = df_evenements_clean[~mask_a_exclure].copy()

    # Nettoyage du texte (balises HTML, entités, espaces...) sur les colonnes textuelles
    for col in COLONNES_TEXTE:
        df_evenements_final[col] = df_evenements_final[col].apply(nettoyer_texte)

    df_evenements_final["texte_description"] = df_evenements_final.apply(
        lambda row: row["longdescription_fr"] if len(row["longdescription_fr"]) > len(row["description_fr"])
        else row["description_fr"],
        axis=1,
    )

    # Écarte les événements avec une description quasi-vide / trop peu informative
    longueurs = df_evenements_final["texte_description"].str.len()
    df_evenements_final = df_evenements_final[longueurs > SEUIL_MIN_DESCRIPTION].copy()

    return df_evenements_final