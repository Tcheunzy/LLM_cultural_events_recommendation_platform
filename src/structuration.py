import pandas as pd


#Fonction de gestion des NaN qui prend une valeur quelconque et une valeur de défaut et qui, en fonction des cas, renvoie l'une ou l'autre
def valeur_ou_defaut(valeur, defaut):
    if valeur is None: #si valeur is None alors on renvoie la valeur de défaut choisie.
        return defaut
    if isinstance(valeur, float) and pd.isna(valeur): #cas des NaN pandas au format float (float("nan")) on renvoie la valeur de défaut choisie.
        return defaut
    if isinstance(valeur, str) and not valeur.strip(): #cas d'une chaine de caractère vide ou ne contenant que des espaces, on renvoie la valeur de défaut choisie.
        return defaut
    return valeur


# formatage des dates pour éviter de lister les multiples dates s'il y en a  pour les évéments récurrents.
def formater_dates(dates, date_min, date_max, nb_occurrences):
    if nb_occurrences == 1:
        debut, _ = dates[0] # Ici on récupere la date de début et on ignore la secode partie du tupple (la date de fin) via _
        return f"le {debut[:10]}" # Si une seule date pour cet événement, on récupère le premier élément du tupple provenant de agg_dates(), et on return les  10 premiers caractères de la chaine iso (2026-04-19T15:00:00+02:00 ici 2026-04-19 (la data seulement))
    elif nb_occurrences <= 5: # Pour tous les events qui ont un nombre de date de 5 ou moins, on récupère le premier éléments du tupple (date de début) et les 10 premiers caractères iso come au dessus (on obtient une liste de daye séparer)
        return "les " + ", ".join(d[0][:10] for d in dates)
    else:
        return f"du {date_min[:10]} au {date_max[:10]} ({nb_occurrences} dates)" # Si le nb de dates de l'event est sup à 5 dans ce cas on donne les 10 premiers catactères iso de la première data et les 10 premeirs caractères iso et de la dernières dates en plus du nombre d'occurence de l'événement.


#fonction d'extraction de potentiel moyen de contacter l'orga de l'event en cas de nécéssité d'information par l'utilisateur.
def extraire_contacts(registration):
    if not isinstance(registration, list): #si la cellule registration n'est pas une vraie liste alors renvoie trois liste vide.
        return {"telephones": [], "emails": [], "liens": []}
    return {
        "telephones": [r["value"] for r in registration if r.get("type") == "phone"], #si liste non vide alors on renvoie un dictionnaire avec clé/liste, garde un téléphone si un "phone"  est renseigné
        "emails": [r["value"] for r in registration if r.get("type") == "email"], #un email si un email  est renseigné
        "liens": [r["value"] for r in registration if r.get("type") == "link"], # un lien si un lien  est renseigné
    }

#fonction de formatage de la méthode d'inscription à l'event
def formater_inscription(contacts): #se base sur la fonction extraire_contacts()
    morceaux = [] #liste vide qui sera remplie par les bouts de phrase à afficher.
    if contacts["telephones"]:
        morceaux.append("téléphone : " + ", ".join(contacts["telephones"]))  #si présence d'un téléphone,on rajoute cette phrase avec le numéro associé
    if contacts["emails"]:
        morceaux.append("email : " + ", ".join(contacts["emails"])) #pareil pour l'email
    if not morceaux:
        return "" #si il n'y a rien de disponible , on n'ajoute rien à la liste morceaux.
    return " Inscription : " + " ; ".join(morceaux) + "." 

def construire_texte(row):
    lieu = row["location_name"] or row["location_city"] or "" #On recupere la localisation de l'event ou on ne retourne rien si aucun des deux premiers champs n'est rempli
    adresse = f", {row['location_address']}" if row["location_address"] else "" # On recupere l'adresse précise s'il y en a une 
    dates_txt = formater_dates(row["dates"], row["date_min"], row["date_max"], row["nb_occurrences"]) #On apllique la fonction créer au dessus pour récuperer les infos sur la date

    mots_cles = ", ".join(row["keywords_fr"]) if isinstance(row["keywords_fr"], list) and row["keywords_fr"] else "" #si la cellule keyword est une liste et qu'elle est non nulle renvoie les valeurs séparé par , sinon ne renvoie rien
    accessibilite = valeur_ou_defaut(row["accessibility_label_fr"], "Pas de précision") #On récupère les informations d'accessibilité à 'event s'il y en a sinon on précise qu'il n'y a pas d'information.

    age_min = valeur_ou_defaut(row.get("age_min"), None) #recupere age min et ne retourne rien si absent
    age_max = valeur_ou_defaut(row.get("age_max"), None) #recupere age max et ne retourne rien si absent
    if age_min is not None and age_max is not None: 
        age_txt = f"de {int(age_min)} à {int(age_max)} ans" #Si on a un age min et max
    elif age_min is not None:
        age_txt = f"à partir de {int(age_min)} ans" # Si on a seulement un âge min
    else:
        age_txt = "non précisé" #valeur renvoyé par défaut

    inscription_txt = formater_inscription(extraire_contacts(row["registration"])) #utilisation des deux fonctions créées précédemment pour récupérer d'abord les contacts liés à l'event puis formater les inscriptions en fonction.

    texte = f"{row['title_fr']}. {row['texte_description']}" #Ici on construit le texte qui va être chunker avec les informations importantes
    if mots_cles:
        texte += f" Catégories : {mots_cles}."
    texte += f" Lieu : {lieu}{adresse}. Dates : {dates_txt}."
    if row["conditions_fr"]:
        texte += f" Conditions : {row['conditions_fr']}."
    texte += f" Accessibilité : {accessibilite}. Âge : {age_txt}."
    texte += inscription_txt
    return texte #On créer notre corpus en récupérant toutes les informations qu'on veut voir vectoriser et qui sera donc chunker.

# Construction du pack de metadata  conserver parmis l'ensemble des features de notre df ici aussi sur row
def construire_metadata(row):
    contacts = extraire_contacts(row["registration"])
    return {
        "uids": row["uids"],
        "titre": row["title_fr"],
        "ville": row["location_city"],
        "quartier": row.get("location_district"),
        "code_postal": row.get("location_postalcode"),
        "departement": row.get("location_department"),
        "dates": row["dates"],
        "date_min": row["date_min"],
        "date_max": row["date_max"],
        "mots_cles": row["keywords_fr"] if isinstance(row["keywords_fr"], list) else [],
        "url": row["canonicalurl"],
        "telephones": contacts["telephones"],
        "emails": contacts["emails"],
        "liens": contacts["liens"],
    }