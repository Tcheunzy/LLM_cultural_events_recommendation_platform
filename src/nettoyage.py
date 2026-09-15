# src/nettoyage.py
import re
import html
from bs4 import BeautifulSoup

#On créer une fonction qui supprime les cellules si il n'y a rien dedans et si on a du texte on le 
# parse avec le html.parser via Beautifoulsup4 puis on récupère ce texte via le html.unescape(soup.get_text) 
# qui remplace toutes les entités html par leur réel symbole et qui récupère le texte en séparant le texte de leures balises avec un espace
def nettoyer_html(texte):
    if not isinstance(texte, str) or not texte.strip():
        return ""
    soup = BeautifulSoup(texte, "html.parser")
    return html.unescape(soup.get_text(separator=" "))

#On normalise les espaces : Cette fonction nettoie et formate un texte pour qu'il ne reste que des espaces simples entre les mots.

def normaliser_espaces(texte):
    texte = texte.replace("\xa0", " ") #Remplace les espaces incassables (fréquents sur le Web ou dans Word) par un espace standard.
    texte = re.sub(r"[\u200b\ufeff]", "", texte) #Supprime les caractères invisibles masqués dans le texte (comme l'espace de largeur nulle \u200b ou le marqueur d'ordre des octets \ufeff).
    texte = re.sub(r"\s+", " ", texte) #re.sub(r"\s+", " ", texte) 
    return texte.strip() #Supprime les espaces restants tout au début et toute la fin du texte, puis renvoie le résultat.

#Ici la fonction orchestratrice des deux précédentes.
def nettoyer_texte(texte):
    return normaliser_espaces(nettoyer_html(texte))
