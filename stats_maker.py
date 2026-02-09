import csv
from datetime import datetime
import re

def decimal_vers_hhmm(heures):
    h = int(heures)
    m = int(round((heures - h) * 60))
    return f"{h:02d}:{m:02d}"


# 0 - Date
# 1 - Jour de la semaine
# 2 - Jour / Nuit
# 3 - FIP
# 4 - FOLIO
# 5 - Horaire
# 6 - Priorité
# 7 - Leader
# 8 - Equipier.iére
# 9 - Troisiéme
# 10 - Ambulance
# 11 - Intervenants
# 12 - Médicalisation
# 13 - Alarme
# 14 - Départ
# 15 - Sur site
# 16 - Québec
# 17 - Hôpital
# 18 - Libre
# 19 - Lieu de PEC
# 20 - Commune de PEC
# 21 - Destination de PEC
# 22 - Type 17
# 23 - Code FIP
# 24 - Motif EST
# 25 - Degré EST
# 26 - NACA
# 27 - Médecin ?
# 28 - Trauma / Médical
# 29 - Protocoles
# 30 - Sexe
# 31 - Age
# 32 - Date de naissance

def temps_moyen_sur_site(lecteur):
    total_temps = 0
    nombre_lignes = 0

    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        # si la colonne Hopital (index 17) est vide, on ignore la ligne
        if not ligne[17].strip():
            continue

        # extraire l'heure depuis la colonne "Sur site" (index 15)
        sur_site_raw = ligne[15].strip()
        tmp = datetime.strptime(sur_site_raw, "%H:%M")
        sur_site_hour = tmp.hour + tmp.minute / 60

        # extraire l'heure depuis la colonne "Quebec" (index 16)
        quebec_raw = ligne[16].strip()
        tmp = datetime.strptime(quebec_raw, "%H:%M")
        quebec_hour = tmp.hour + tmp.minute / 60
        
        nombre_lignes += 1
        temps_sur_site = quebec_hour - sur_site_hour
        if temps_sur_site < 0:
            temps_sur_site += 24  # gérer les cas où l'heure de Québec est le lendemain
        total_temps += temps_sur_site
        # print(f"Sur site = {sur_site_hour}, Quebec = {quebec_hour}, Temps sur site = {decimal_vers_hhmm(temps_sur_site)}")

    print(f"Nombre de lignes (interventions) comptées : {nombre_lignes}")
    print(f"Temps total sur site : {decimal_vers_hhmm(total_temps)}")
    print(f"Temps moyen sur site : {decimal_vers_hhmm(total_temps / nombre_lignes)}")






# chemin_fichier = "janvier 2026.csv"
chemin_fichier = "decembre 2025.csv"

with open(chemin_fichier, newline="", encoding="utf-8") as csvfile:
    lecteur = csv.reader(csvfile, delimiter=";")

    # next(lecteur, None)  # saute l'en-tête
    # for ligne in lecteur:
    #     if ligne:
    #         print(ligne[0])

    temps_moyen_sur_site(lecteur)



# idees stats
# 
# 
# 
# temps sur site
# pourcentage p1p2p3s1s1
# EST les plus courrant
# repatition par ambulance
# age des patients (boite a moustache)
# repartition des nacas
# 
# le plus d'intervention en 2 et 5h
# personne avec le plus de naca haut
# personne avec le plus de naca bas
# p3 qui finissent en naca haut 
# qui a fait le plus d'interventions
# pourcentga de leader/secondage
# collegue preferé
# le binome avec le plus d'interventions




