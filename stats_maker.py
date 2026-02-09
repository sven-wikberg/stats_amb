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
# 26 - Degré EST
# 27 - NACA
# 28 - Médecin ?
# 29 - Trauma / Médical
# 30 - Protocoles
# 31 - Sexe
# 32 - Age
# 33 - Date de naissance

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

    # print(f"Nombre de lignes (interventions) comptées : {nombre_lignes}")
    # print(f"Temps total sur site : {decimal_vers_hhmm(total_temps)}")
    print(f"Temps moyen sur site : {decimal_vers_hhmm(total_temps / nombre_lignes)}")

def repartition_priorites(lecteur):
    priorites = {}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        priorite = ligne[6].strip()
        if priorite:
            if priorite not in priorites:
                priorites[priorite] = 0
            priorites[priorite] += 1

    total_interventions = sum(priorites.values())
    for p, count in priorites.items():
        pourcentage = (count / total_interventions) * 100
        print(f"Priorité {p} : {count} interventions ({pourcentage:.2f}%)")

def repartition_ambulances(lecteur):
    ambulances = {}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        ambulance = ligne[10].strip()[2:]  # on enlève les 2 premiers caractères "60" pour ne garder que le numéro
        if ambulance:
            if ambulance not in ambulances:
                ambulances[ambulance] = 0
            ambulances[ambulance] += 1

    total_interventions = sum(ambulances.values())
    for a, count in ambulances.items():
        pourcentage = (count / total_interventions) * 100
        print(f"Ambulance {a} : {count} interventions ({pourcentage:.2f}%)")

def repartition_nacas(lecteur):
    nacas = {}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        naca = ligne[27].strip()
        if naca:
            if naca not in nacas:
                nacas[naca] = 0
            nacas[naca] += 1

    total_interventions = sum(nacas.values())
    for n, count in nacas.items():
        pourcentage = (count / total_interventions) * 100
        print(f"NACA {n} : {count} interventions ({pourcentage:.2f}%)")

# chemin_fichier = "janvier 2026.csv"
chemin_fichier = "decembre 2025.csv"

with open(chemin_fichier, newline="", encoding="utf-8") as csvfile:
    lecteur = csv.reader(csvfile, delimiter=";")

    # temps_moyen_sur_site(lecteur)
    # repartition_priorites(lecteur)
    # repartition_ambulances(lecteur)
    repartition_nacas(lecteur)



# idees stats
# 
# 
# 
# DONE : temps sur site
# DONE : pourcentage p1p2p3s1s1
# DONE : repartition par ambulance
# DONE : repartition des nacas
#
# TODO : output avec latek ou autre pour faire des jolis graphiques
#
# age des patients (boite a moustache)
# EST les plus courant
# 
# le plus d'intervention en 2 et 5h
# personne avec le plus de naca haut
# personne avec le plus de naca bas
# p3 qui finissent en naca haut 
# qui a fait le plus d'interventions
# pourcentga de leader/secondage
# collegue preferé
# le binome avec le plus d'interventions




