"""
Génère le jeu de questions/réponses annoté pour l'évaluation du chatbot RAG
(Projet 9 - Puls-Events / Fête de la Bretagne).

Usage :
    uv run python build_qa_testset.py

Produit : data/qa_testset.csv avec les colonnes :
    - question           : la question posée au chatbot
    - reponse_reference   : la réponse attendue, validée manuellement
    - categorie           : "factuelle_simple" | "multi_critere" | "hors_perimetre"
"""

import csv
from pathlib import Path

QA_TESTSET = [
    # --- Questions factuelles simples ---
    {
        "question": "À quelle heure et où a lieu la \"Lecture à l'heure du goûter\" à Vitré ?",
        "reponse_reference": "Mercredi 20 mai de 17h à 17h30, à la médiathèque du Quai des arts, "
                              "1 rue du Bourg-aux-Moines, 35500 Vitré.",
        "categorie": "factuelle_simple",
    },
    {
        "question": "Quand se déroule le \"Fest deizh\" à Saint-M'Hervé ?",
        "reponse_reference": "Dimanche 24 mai de 18h à 20h, à la base de loisirs de la Haute-Vilaine "
                              "(La ville cuite, 35500 Saint-M'Hervé).",
        "categorie": "factuelle_simple",
    },
    {
        "question": "Quel est le tarif du spectacle de \"Fêtez la Bretagne à Pont l'Abbé\" ?",
        "reponse_reference": "L'après-midi est gratuite ; le spectacle en soirée est payant, "
                              "entre 5 et 25 euros.",
        "categorie": "factuelle_simple",
    },
    {
        "question": "À quelle adresse et quel jour a lieu \"Fougères fête la Bretagne\" ?",
        "reponse_reference": "Le 19 mai à partir de 16h, Place Aristide Briand à Fougères, "
                              "avec une soirée au 3F.",
        "categorie": "factuelle_simple",
    },
    {
        "question": "Sur quelle période s'étale \"Brest La Fest'Yves 2026\" ?",
        "reponse_reference": "Du jeudi 14 au dimanche 24 mai 2026, dans le quartier de Recouvrance "
                              "/ rue Saint-Malo à Brest.",
        "categorie": "factuelle_simple",
    },
    # --- Questions multi-critères ---
    {
        "question": "Y a-t-il un événement autour de la danse bretonne dans les Côtes-d'Armor "
                    "fin mai 2026 ?",
        "reponse_reference": "Oui, la \"Fête de la Bretagne à Pléneuf-Val-André\" (22370) le 24 mai, "
                              "avec initiation à la danse bretonne dès 14h par le cercle celtique "
                              "Les Gastadours de Lamballe.",
        "categorie": "multi_critere",
    },
    {
        "question": "Quels événements en Ille-et-Vilaine proposent de la musique bretonne "
                    "autour du 20 mai 2026 ?",
        "reponse_reference": "Le \"Fest deizh\" à Saint-M'Hervé (24 mai) et \"Fougères fête la "
                              "Bretagne\" (19 mai, avec le duo Car et Ment).",
        "categorie": "multi_critere",
    },
    {
        "question": "Existe-t-il un événement accessible aux personnes à mobilité réduite dans "
                    "le Finistère à cette période ?",
        "reponse_reference": "Oui, \"Fêtez la Bretagne à Pont l'Abbé\" (29120, 23 mai) précise "
                              "une accessibilité handicap moteur.",
        "categorie": "multi_critere",
    },
    {
        "question": "Quel événement combine langue bretonne et spectacle musical dans la même "
                    "journée ?",
        "reponse_reference": "\"Fêtez la Bretagne à Pont l'Abbé\" (23 mai) : initiation à la langue "
                              "bretonne l'après-midi, spectacle musical en soirée.",
        "categorie": "multi_critere",
    },
    {
        "question": "Quel événement gratuit et familial est prévu pour les jeunes enfants en "
                    "Ille-et-Vilaine ?",
        "reponse_reference": "La \"Lecture à l'heure du goûter\" à Vitré (20 mai), entrée libre, "
                              "à partir de 3 ans.",
        "categorie": "multi_critere",
    },
    # --- Questions hors périmètre (réponse attendue : refus honnête) ---
    {
        "question": "Quels événements de la Fête de la Bretagne sont prévus à Nantes en 2026 ?",
        "reponse_reference": "Aucune information disponible — Nantes est en Pays de la Loire, "
                              "hors du périmètre régional Bretagne couvert par la base.",
        "categorie": "hors_perimetre",
    },
    {
        "question": "Y a-t-il une journée de recrutement dans le secteur culturel prévue à "
                    "Rennes ce mois-ci ?",
        "reponse_reference": "Aucune information disponible — ce type d'événement est "
                              "explicitement exclu du filtrage culturel.",
        "categorie": "hors_perimetre",
    },
    {
        "question": "Quel événement autour de la Bretagne est prévu en 2028 ?",
        "reponse_reference": "Aucune information disponible — la base ne couvre que les "
                              "événements dans une fenêtre d'environ un an.",
        "categorie": "hors_perimetre",
    },
]


def main() -> None:
    output_path = Path("data") / "qa_testset.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["question", "reponse_reference", "categorie"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(QA_TESTSET)

    print(f"{len(QA_TESTSET)} questions écrites dans {output_path}")
    counts = {}
    for row in QA_TESTSET:
        counts[row["categorie"]] = counts.get(row["categorie"], 0) + 1
    for categorie, n in counts.items():
        print(f"  - {categorie} : {n}")


if __name__ == "__main__":
    main()