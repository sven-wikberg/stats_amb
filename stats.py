import csv
from datetime import datetime
import re
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

OUTPUT_DIR = "output"
CSV_DATA_FILE = "janvier 2026.csv"
# CSV_DATA_FILE = "decembre 2025.csv"
DATA_DIR = "data"
OUTPUT_PATH = f"{OUTPUT_DIR}/rapport_qualite - {CSV_DATA_FILE.replace('.csv', '.pdf')}"
DATA_PATH = f"{DATA_DIR}/{CSV_DATA_FILE}"


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

    # print(f"Nombre de lignes (interventions) comptées : {nombre_lignes}")
    # print(f"Temps total sur site : {decimal_vers_hhmm(total_temps)}")
    print(
        f"Temps moyen sur site : {decimal_vers_hhmm(total_temps / nombre_lignes)}")


def repartition_priorites(lecteur):
    priorites = {"P1": 0, "P2": 0, "P3": 0,
                 "S1 feux bleus": 0, "S1 sans feux bleus": 0}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        priorite = ligne[6].strip()
        if priorite:
            if priorite not in priorites:
                priorites[priorite] = 0
            priorites[priorite] += 1

    total_interventions = sum(priorites.values())
    # for p, count in priorites.items():
    #     pourcentage = (count / total_interventions) * 100
    #     print(f"Priorité {p} : {count} interventions ({pourcentage:.2f}%)")
    return priorites


def create_graph_priorites(priorites):
    total_interventions = sum(priorites.values())
    palette_priorite = {
        "P1": "#D62828",
        "P2": "#F2C94C",
        "P3": "#27AE60",
        "S1 feux bleus": "#D62828",
        "S1 sans feux bleus": "#E67E22",
        "S2": "#F2C94C"
    }
    plt.figure()
    plt.bar(priorites.keys(), priorites.values(), color=[
            palette_priorite[k] for k in priorites.keys()], edgecolor='black')
    # print percentage on each bar
    for i, v in enumerate(priorites.values()):
        pourcentage = (v / total_interventions) * \
            100 if total_interventions > 0 else 0
        plt.text(i, v + 2, f"{pourcentage:.2f}%", ha='center')
    plt.title("Répartition des interventions par priorités")
    plt.ylabel("Nombre d'interventions")
    plt.xticks(rotation=15)
    plt.tight_layout()

    graph_path = "graph_priorites.png"
    plt.savefig(graph_path)
    plt.close()


def repartition_ambulances(lecteur):
    ambulances = {"704": 0, "705": 0, "706": 0, "707": 0, "708": 0, "709": 0}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        # on enlève les 2 premiers caractères "60" pour ne garder que le numéro
        ambulance = ligne[10].strip()[2:]
        if ambulance:
            if ambulance not in ambulances:
                ambulances[ambulance] = 0
            ambulances[ambulance] += 1

    total_interventions = sum(ambulances.values())
    # for a, count in ambulances.items():
    #     pourcentage = (count / total_interventions) * 100
    #     print(f"Ambulance {a} : {count} interventions ({pourcentage:.2f}%)")
    return ambulances


def create_graph_ambulances(ambulances):
    total_interventions = sum(ambulances.values())
    plt.figure()
    plt.bar(ambulances.keys(), ambulances.values(), color=[
            '#1D3557', '#457B9D', '#1D3557', '#457B9D', '#1D3557', '#457B9D'], edgecolor='black')
    # print percentage on each bar
    for i, v in enumerate(ambulances.values()):
        pourcentage = (v / total_interventions) * \
            100 if total_interventions > 0 else 0
        plt.text(i, v + 2, f"{pourcentage:.2f}%", ha='center')
    plt.title("Répartition interventions par ambulance")
    plt.ylabel("Nombre d'interventions")
    plt.xticks(rotation=15)
    plt.tight_layout()

    graph_path = "graph_ambulances.png"
    plt.savefig(graph_path)
    plt.close()


def repartition_nacas(lecteur):
    nacas = {"0": 0, "1": 0, "2": 0, "3": 0,
             "4": 0, "5": 0, "6": 0, "7": 0, "9": 0}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        naca = ligne[26].strip()
        if naca:
            if naca not in nacas:
                nacas[naca] = 0
            nacas[naca] += 1

    total_interventions = sum(nacas.values())
    # for n, count in nacas.items():
    #     pourcentage = (count / total_interventions) * 100
    #     print(f"NACA {n} : {count} interventions ({pourcentage:.2f}%)")
    return nacas


def create_graph_nacas(nacas):
    total_interventions = sum(nacas.values())
    palette_naca = {
        '0': "#6FCF97",
        '1': "#27AE60",
        '2': "#F2C94C",
        '3': "#F2994A",
        '4': "#E67E22",
        '5': "#D62828",
        '6': "#1D3557",
        '7': "#000000",
        '9': "#FFFFFF"
    }

    plt.figure()
    plt.bar(nacas.keys(), nacas.values(), color=[
            palette_naca[k] for k in nacas.keys()], edgecolor='black')
    # print percentage on each bar
    for i, v in enumerate(nacas.values()):
        pourcentage = (v / total_interventions) * \
            100 if total_interventions > 0 else 0
        plt.text(i, v + 2, f"{pourcentage:.2f}%", ha='center')
    plt.title("Répartition interventions par NACA")
    plt.ylabel("Nombre d'interventions")
    plt.xticks(rotation=15)
    plt.tight_layout()

    graph_path = "graph_nacas.png"
    plt.savefig(graph_path)
    plt.close()


def generate_pdf_report():
    doc = SimpleDocTemplate(OUTPUT_PATH, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Ajouter un titre
    title = Paragraph(
        "Rapport de Qualité - Interventions Ambulance", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.5 * inch))

    # Ajouter les graphiques
    for graph in ["graph_priorites.png", "graph_ambulances.png", "graph_nacas.png"]:
        img = Image(graph, width=6 * inch, height=4 * inch)
        elements.append(img)
        elements.append(Spacer(1, 0.5 * inch))

    doc.build(elements)


# chemin_fichier = "janvier 2026.csv"
chemin_fichier = DATA_PATH
print(f"Lecture du fichier CSV : {chemin_fichier}")

with open(chemin_fichier, newline="", encoding="utf-8") as csvfile:

    # ==== CODE PRINCIPAL ====

    # print("Génération des graphiques...")

    # lecteur = csv.reader(csvfile, delimiter=";")
    # create_graph_priorites(repartition_priorites(lecteur))
    # print("Graphique des priorités généré.")

    # csvfile.seek(0)  # revenir au début du fichier pour relire les données
    # lecteur = csv.reader(csvfile, delimiter=";")
    # create_graph_ambulances(repartition_ambulances(lecteur))
    # print("Graphique des ambulances généré.")

    # csvfile.seek(0)  # revenir au début du fichier pour relire les données
    # lecteur = csv.reader(csvfile, delimiter=";")
    # create_graph_nacas(repartition_nacas(lecteur))
    # print("Graphique des NACA généré.")

    # generate_pdf_report()
    # print(f"Rapport PDF généré : {OUTPUT_PATH}")

    # === TESTS ===

    lecteur = csv.reader(csvfile, delimiter=";")
    temps_moyen_sur_site(lecteur)

    # === TODO ===

    # DONE : temps sur site
    # DONE : pourcentage p1p2p3s1s1
    # DONE : repartition par ambulance
    # DONE : repartition des nacas
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
