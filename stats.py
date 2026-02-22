import csv
from datetime import datetime
import re
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
import numpy as np

OUTPUT_DIR = "output"
CSV_DATA_FILE = "decembre 2025.csv"
CSV_DATA_FILE = "janvier 2026.csv"
DATA_DIR = "data"
OUTPUT_PATH = f"{OUTPUT_DIR}/rapport_qualite - {CSV_DATA_FILE.replace('.csv', '.pdf')}"
DATA_PATH = f"{DATA_DIR}/{CSV_DATA_FILE}"

GRAPH_PRIORITES_PATH = f"{OUTPUT_DIR}/graph_priorites.png"
GRAPH_AMBULANCES_PATH = f"{OUTPUT_DIR}/graph_ambulances.png"
GRAPH_NACAS_PATH = f"{OUTPUT_DIR}/graph_nacas.png"
GRAPH_AGES_PATH = f"{OUTPUT_DIR}/graph_ages.png"
GRAPH_INTER_BY_HEURE_PATH = f"{OUTPUT_DIR}/graph_inter_by_heure.png"


def decimal_vers_hhmm(heures):
    h = int(heures)
    m = int(round((heures - h) * 60))
    if h == 0 and m == 1:
        return "1 minute"
    if h == 0:
        return f"{m:02d} minutes"
    return f"{h:02d} heures et {m:02d} minutes"


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
# 31 - Date de naissance
# 32 - Age

def get_temps_sur_site(lecteur):
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
    # print(
    #     f"Temps moyen sur site : {decimal_vers_hhmm(total_temps / nombre_lignes)}")
    return {"total_temps_sur_site": total_temps, "nombre_interventions": nombre_lignes, "moyenne": total_temps / nombre_lignes if nombre_lignes > 0 else 0}


def get_naca_by_personne(lecteur):
    naca_par_personne = {}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        leader = ligne[7].strip()
        equipier = ligne[8].strip()
        naca = ligne[26].strip()

        if leader and naca:
            if leader not in naca_par_personne:
                naca_par_personne[leader] = []
            naca_par_personne[leader].append(naca)

        if equipier and naca:
            if equipier not in naca_par_personne:
                naca_par_personne[equipier] = []
            naca_par_personne[equipier].append(naca)

    return naca_par_personne


def get_naca_of_p3(lecteur):
    naca_of_p3 = {"0": 0, "1": 0, "2": 0, "3": 0,
                  "4": 0, "5": 0, "6": 0, "7": 0, "9": 0}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        priorite = ligne[6].strip()
        naca = ligne[26].strip()

        if priorite == "P3" and naca:
            naca_of_p3[naca] += 1

    return naca_of_p3


def repartition_motif_est(lecteur):
    motifs = {}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        motif = ligne[24].strip()
        if motif[:4]:
            if motif not in motifs:
                motifs[motif] = 0
            motifs[motif] += 1

    total_interventions = sum(motifs.values())
    motifs = dict(
        sorted(motifs.items(), key=lambda item: item[1], reverse=True))
    return motifs


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

    graph_path = GRAPH_PRIORITES_PATH
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
    plt.tight_layout()

    graph_path = GRAPH_AMBULANCES_PATH
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
    plt.xlabel("NACA")
    plt.tight_layout()

    graph_path = GRAPH_NACAS_PATH
    plt.savefig(graph_path)
    plt.close()


def create_graph_heures(inter_by_heure):
    palette_heures = {
        # Nuit profonde
        '00': "#0B132B",
        '01': "#0B132B",
        '02': "#1C2541",
        '03': "#1C2541",
        '04': "#3A506B",

        # Aube
        '05': "#5BC0BE",
        '06': "#89C2D9",
        '07': "#A9D6E5",

        # Matin
        '08': "#F1FAEE",
        '09': "#FFE8A1",
        '10': "#FFD166",
        '11': "#FFC43D",

        # Midi (maximum activité lumineuse)
        '12': "#FFB703",
        '13': "#FFB703",
        '14': "#FFD166",

        # Après-midi
        '15': "#F4A261",
        '16': "#E76F51",
        '17': "#D62828",

        # Soirée
        '18': "#BC4749",
        '19': "#6D597A",
        '20': "#355070",

        # Nuit
        '21': "#1D3557",
        '22': "#1D3557",
        '23': "#0B132B"
    }

    plt.figure()
    plt.bar(inter_by_heure.keys(), inter_by_heure.values(), color=[
            palette_heures[k] for k in inter_by_heure.keys()], edgecolor='black')
    plt.title("Nombre d'interventions par heure")
    plt.ylabel("Nombre d'interventions")
    plt.xlabel("Heure")
    plt.tight_layout()

    graph_path = GRAPH_INTER_BY_HEURE_PATH
    plt.savefig(graph_path)
    plt.close()


def get_age_patients(lecteur):
    ages = []
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        age_str = ligne[32].strip()
        date_de_naissance_str = ligne[31].strip()
        if age_str.isdigit() and date_de_naissance_str != "":
            ages.append(int(age_str))

    return ages


def get_nacas_hauts(lecteur):
    nacas_by_personne = get_naca_by_personne(lecteur)
    nb_nacas_haut = {}
    nb_nacas = {}
    for personne, nacas in nacas_by_personne.items():
        # print(f"{personne} : {nacas}")
        for naca in nacas:
            if naca in ["5", "6", "7"]:
                if personne not in nb_nacas_haut:
                    nb_nacas_haut[personne] = 0
                nb_nacas_haut[personne] += 1
            if personne not in nb_nacas:
                nb_nacas[personne] = 0
            nb_nacas[personne] += 1
    output = {}
    for personne in nb_nacas_haut:
        output[personne] = (nb_nacas[personne], nb_nacas_haut[personne], (
            nb_nacas_haut[personne] / nb_nacas[personne]) if nb_nacas[personne] > 0 else 0)
    sorted_output = dict(
        sorted(output.items(), key=lambda item: item[1][2], reverse=True))
    return sorted_output


def get_nacas_bas(lecteur):
    nacas_by_personne = get_naca_by_personne(lecteur)
    nb_nacas_bas = {}
    nb_nacas = {}
    for personne, nacas in nacas_by_personne.items():
        # print(f"{personne} : {nacas}")
        for naca in nacas:
            if naca in ["0", "1", "9"]:
                if personne not in nb_nacas_bas:
                    nb_nacas_bas[personne] = 0
                nb_nacas_bas[personne] += 1
            if personne not in nb_nacas:
                nb_nacas[personne] = 0
            nb_nacas[personne] += 1
    output = {}
    for personne in nb_nacas_bas:
        output[personne] = (nb_nacas[personne], nb_nacas_bas[personne], (
            nb_nacas_bas[personne] / nb_nacas[personne]) if nb_nacas[personne] > 0 else 0)
    sorted_output = dict(
        sorted(output.items(), key=lambda item: item[1][2], reverse=True))
    return sorted_output


def create_graph_ages(ages):
    # Calcul des stats
    age_moyen = np.mean(ages)
    age_median = np.median(ages)
    age_min = np.min(ages)
    age_max = np.max(ages)
    nb_patients = len(ages)

    plt.figure(figsize=(6, 4))

    # Violin plot horizontal
    parts = plt.violinplot(
        ages,
        vert=False,
        showmeans=False,
        showmedians=False,
        showextrema=True
    )

    # Ligne médiane
    plt.axvline(age_median, linestyle='-', linewidth=2,
                label=f"Age médian: {age_median:.1f}")

    # Ligne moyenne
    plt.axvline(age_moyen, linestyle='--', linewidth=2,
                label=f"Age moyen: {age_moyen:.1f}")

    # Lignes min et max
    plt.axvline(age_min, linestyle=' ', label=f"Age minimum: {age_min}")
    plt.axvline(age_max, linestyle=' ', label=f"Age maximum: {age_max}")
    plt.axvline(0, linestyle=' ', label=f"Nombre de patients: {nb_patients}")

    plt.yticks([])  # enlève l'axe Y inutile
    plt.xlabel("Âge")
    plt.title("Distribution des âges")

    plt.legend(loc='upper left')
    plt.tight_layout()

    plt.savefig(GRAPH_AGES_PATH, dpi=300)
    plt.close()


def get_nb_inter_by_heure(lecteur):
    nb_inter_by_heure = {str(h).zfill(2): 0 for h in range(24)}
    next(lecteur, None)  # saute l'en-tête

    for ligne in lecteur:
        horaire_str = ligne[15].strip()
        if re.match(r'^\d{2}:\d{2}$', horaire_str):
            heure = horaire_str.split(":")[0]
            nb_inter_by_heure[heure] += 1

    return nb_inter_by_heure


def generate_pdf_report(nombre_interventions, temps_moyen_sur_site, age_moyen, motifs_EST, nacas_bas, nacas_hauts, nacas_p3):
    doc = SimpleDocTemplate(OUTPUT_PATH, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    style_texte = {'texte_grand': ParagraphStyle(
        'texte_grand',
        parent=styles['Normal'],
        fontSize=14,     # taille du texte
        leading=18       # interligne
    ), 'texte_normal': ParagraphStyle(
        'texte_normal',
        parent=styles['Normal'],
        fontSize=12,     # taille du texte
        leading=16       # interligne
    )}

    # Ajouter un titre
    title = Paragraph(
        "Rapport Mensuel - Interventions Ambulance", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.5 * inch))

    # Ajouter le nombre d'interventions
    texte_nombre_interventions = (
        f"Ce mois, ACE a effectué "
        f"<font color='#D62828'><b>{nombre_interventions} interventions</b></font> "
        f"entre l'urgence et la P3."
    )
    elements.append(Paragraph(texte_nombre_interventions,
                    style_texte['texte_grand']))
    elements.append(Spacer(1, 0.5 * inch))

    # Ajouter les motifs EST les plus courants
    texte_intro_motifs_est = "Les motifs EST les plus courants étaient : <br/>"
    elements.append(Paragraph(texte_intro_motifs_est,
                    style_texte['texte_grand']))

    nb_inter_motif_est = sum(motifs_EST.values())
    texte_motifs_est = ""
    i = 0
    for motif, count in motifs_EST.items():
        if motif[:4] == "0000":
            continue  # on ignore les motifs vides ou non renseignés
        texte_motifs_est += f"{i+1}. {motif} avec <b>{(count / nb_inter_motif_est) * 100:.1f}%</b> ({count}) des interventions <br/>"
        if i >= 4:  # on affiche les 5 motifs les plus courants
            break
        i = i + 1
    elements.append(Paragraph(texte_motifs_est, style_texte['texte_normal']))
    elements.append(Spacer(1, 0.5 * inch))

    # Ajouter le temps moyen sur site
    texte_temps_moyen = (
        f"Et en moyenne, nous avons passé "
        f"<font color='#D62828'><b>{decimal_vers_hhmm(temps_moyen_sur_site)}</b></font>"
        f" sur site."
    )
    elements.append(Paragraph(texte_temps_moyen, style_texte['texte_grand']))
    elements.append(Spacer(1, 0.5 * inch))

    # Ajouter une introduction pour expliquer les graphiques
    introduction_graphique = "Ci-dessous les graphiques de répartition des interventions par priorités, ambulances et NACAs."
    elements.append(Paragraph(introduction_graphique,
                    style_texte['texte_grand']))

    # Ajouter les graphiques

    # Graphique des ambulances
    img = Image(GRAPH_AMBULANCES_PATH, width=6 * inch, height=4 * inch)
    elements.append(img)
    elements.append(Spacer(1, 0.5 * inch))

    # Graphique des priorités
    img = Image(GRAPH_PRIORITES_PATH, width=6 * inch, height=4 * inch)
    elements.append(img)
    elements.append(Spacer(1, 0.5 * inch))

    # Naca pour la p3
    total_nacas_p3 = sum(nacas_p3.values())
    p3_naca_hauts = sum(nacas_p3[naca] for naca in ["4", "5", "6", "7"])
    texte_naca_p3 = f"Ce mois ci, en P3, <b>{p3_naca_hauts}</b> interventions sur <b>{total_nacas_p3}</b> ont été classées en NACA 4+, soit <b>{(p3_naca_hauts / total_nacas_p3) * 100:.1f}%</b> des P3."
    elements.append(Paragraph(texte_naca_p3, style_texte['texte_grand']))
    elements.append(Spacer(1, 0.5 * inch))

    # Graphique des NACAs
    img = Image(GRAPH_NACAS_PATH, width=6 * inch, height=4 * inch)
    elements.append(img)
    elements.append(Spacer(1, 0.5 * inch))

    # Naca bas et haut par personne
    texte_nacas_par_personne = "Voici les 3 personnes qui se démarquent par leur nombre d'intervention avec des NACAs bas (0, 1, 9) : <br/>"
    i = 0
    for personne, (nb_nacas, nb_nacas_bas, pourcentage) in nacas_bas.items():
        texte_nacas_par_personne += f"{i+1}. <b>{pourcentage:.1%}</b> des interventions de <b>{personne}</b> ({nb_nacas_bas}/{nb_nacas})<br/>"
        if i >= 2:  # on affiche les 3 permiers
            break
        i = i + 1
    texte_nacas_par_personne += "<br/>Et voici les 3 personnes qui se démarquent par leur nombre d'intervention avec des NACAs hauts (5, 6, 7) : <br/>"
    i = 0
    for personne, (nb_nacas, nb_nacas_haut, pourcentage) in nacas_hauts.items():
        texte_nacas_par_personne += f"{i+1}. <b>{pourcentage:.1%}</b> des interventions de <b>{personne}</b> ({nb_nacas_haut}/{nb_nacas})<br/>"
        if i >= 2:  # on affiche les 3 permiers
            break
        i = i + 1
    elements.append(Paragraph(texte_nacas_par_personne,
                    style_texte['texte_normal']))
    elements.append(Spacer(1, 0.5 * inch))

    # Texte intro pour le graphique des âges
    texte_temps_moyen = (
        f"Nos patients avaient en moyenne "
        f"<font color='#D62828'><b>{age_moyen:.1f}</b></font>"
        f" ans. Ci-dessous, la répartition détaillée de leurs âges."
    )
    elements.append(Paragraph(texte_temps_moyen, style_texte['texte_grand']))
    elements.append(Spacer(1, 0.5 * inch))

    # Graphique des âges
    img = Image(GRAPH_AGES_PATH, width=6 * inch, height=4 * inch)
    elements.append(img)
    elements.append(Spacer(1, 0.5 * inch))

    doc.build(elements)


def main():
    chemin_fichier = DATA_PATH
    print(f"Lecture du fichier CSV : {chemin_fichier}")

    with open(chemin_fichier, newline="", encoding="utf-8") as csvfile:

        print("Calcul du nombre d'interventions...")
        lecteur = csv.reader(csvfile, delimiter=";")
        nb_interventions_total = len(
            list(lecteur)) - 1  # pour sauter l'en-tête

        print("Génération des graphiques...")
        # Génération du graphique des priorités
        csvfile.seek(0)  # revenir au début du fichier pour relire les données
        lecteur = csv.reader(csvfile, delimiter=";")
        lecteur = csv.reader(csvfile, delimiter=";")
        create_graph_priorites(repartition_priorites(lecteur))
        print("Graphique des priorités généré.")

        # Génération du graphique des ambulances
        csvfile.seek(0)  # revenir au début du fichier pour relire les données
        lecteur = csv.reader(csvfile, delimiter=";")
        create_graph_ambulances(repartition_ambulances(lecteur))
        print("Graphique des ambulances généré.")

        # Génération du graphique des NACAs
        csvfile.seek(0)  # revenir au début du fichier pour relire les données
        lecteur = csv.reader(csvfile, delimiter=";")
        create_graph_nacas(repartition_nacas(lecteur))
        print("Graphique des NACA généré.")

        # Génération du graphique des âges
        csvfile.seek(0)  # revenir au début du fichier pour relire les données
        lecteur = csv.reader(csvfile, delimiter=";")
        ages = get_age_patients(lecteur)
        create_graph_ages(ages)
        print("Graphique des âges généré.")

        # Calcul du temps sur site
        csvfile.seek(0)  # revenir au début du fichier pour relire les données
        lecteur = csv.reader(csvfile, delimiter=";")
        temps_sur_site = get_temps_sur_site(lecteur)
        print("Calcul du temps sur site terminé.")

        # Calcul du nombre d'interventions par motif EST
        csvfile.seek(0)  # revenir au début du fichier pour relire les données
        lecteur = csv.reader(csvfile, delimiter=";")
        motifs_EST = repartition_motif_est(lecteur)
        print("Calcul de la répartition des motifs EST terminé.")

        # Calcul du nombre de NACAs bas par personne
        csvfile.seek(0)  # revenir au début du fichier pour relire les données
        lecteur = csv.reader(csvfile, delimiter=";")
        nacas_bas = get_nacas_bas(lecteur)
        print("Calcul du nombre de NACAs bas par personne terminé.")

        # Calcul du nombre de NACAs hauts par personne
        csvfile.seek(0)  # revenir au début du fichier pour relire les données
        lecteur = csv.reader(csvfile, delimiter=";")
        nacas_hauts = get_nacas_hauts(lecteur)
        print("Calcul du nombre de NACAs hauts par personne terminé.")

        # Calcul du nombre des nacas pour la p3
        csvfile.seek(0)  # revenir au début du fichier pour relire les données
        lecteur = csv.reader(csvfile, delimiter=";")
        nacas_p3 = get_naca_of_p3(lecteur)
        print("Calcul du nombre de NACAs pour les P3 terminé.")

        generate_pdf_report(
            nb_interventions_total, temps_sur_site['moyenne'], age_moyen=np.mean(ages), motifs_EST=motifs_EST, nacas_bas=nacas_bas, nacas_hauts=nacas_hauts, nacas_p3=nacas_p3)
        print(f"Rapport PDF généré : {OUTPUT_PATH}")


def tests():
    chemin_fichier = DATA_PATH
    print(f"Lecture du fichier CSV : {chemin_fichier}")

    with open(chemin_fichier, newline="", encoding="utf-8") as csvfile:
        lecteur = csv.reader(csvfile, delimiter=";")
        inter_by_heure = get_nb_inter_by_heure(lecteur)
        print("Nombre d'interventions par heure :")
        print(inter_by_heure)
        for heure, count in inter_by_heure.items():
            print(f"{heure}h : {count} interventions")
        create_graph_heures(inter_by_heure)
        print("Graphique des interventions par heure généré.")


# ====== EXECUTION =====


# main()
tests()

# === TODO ===

# DONE : temps sur site
# DONE : pourcentage p1p2p3s1s1
# DONE : repartition par ambulance
# DONE : repartition des nacas
# DONE : age des patients (boite a moustache)
# DONE : EST les plus courant
# DONE : personne avec le plus de naca haut
# DONE : personne avec le plus de naca bas
# DONE : p3 qui finissent en naca haut
#
#
# le plus d'intervention en 2 et 5h
#
#
# qui a fait le plus d'interventions
# pourcentga de leader/secondage
# le binome avec le plus d'interventions
# sur place le plus court avec transport
# prise en charge avc la plus rapide
# polytrauma le plus rapide
# le plus d'oh
# ple plus de ped
# inter la plus longue
# 42 le plus long
