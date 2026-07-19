import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

# ====== TES DONNÉES ======
data = {'0': 2, '1': 22, '2': 169, '3': 177,
        '4': 125, '5': 15, '6': 2, '7': 2, '9': 10}

# ====== 1. GRAPH =========

# # ===== 1.1. Répartition des interventions par priorités ======
# tmp_total = sum(data.values())
# palette_priorite = {
#     "P1": "#D62828",
#     "P2": "#F2C94C",
#     "P3": "#27AE60",
#     "S1 feux bleus": "#D62828",
#     "S1 sans feux bleus": "#E67E22"
# }
# plt.figure()
# plt.bar(data.keys(), data.values(), color=[palette_priorite[k] for k in data.keys()], edgecolor='black')
# # print percentage on each bar
# for i, v in enumerate(data.values()):
#     pourcentage = (v / tmp_total) * 100
#     plt.text(i, v + 2, f"{pourcentage:.2f}%", ha='center')
# plt.title("Répartition des interventions par priorités")
# plt.ylabel("Nombre d'interventions")
# plt.xticks(rotation=15)
# plt.tight_layout()

# graph_path = "graph.png"
# plt.savefig(graph_path)
# plt.close()

# # ===== 1.2. Répartition des interventions par ambulances ======
# tmp_total = sum(data.values())
# plt.figure()
# plt.bar(data.keys(), data.values(), color=[
#         '#1D3557', '#457B9D', '#1D3557', '#457B9D', '#1D3557', '#457B9D'], edgecolor='black')
# # print percentage on each bar
# for i, v in enumerate(data.values()):
#     pourcentage = (v / tmp_total) * 100
#     plt.text(i, v + 2, f"{pourcentage:.2f}%", ha='center')
# plt.title("Répartition interventions par ambulance")
# plt.ylabel("Nombre d'interventions")
# plt.xticks(rotation=15)
# plt.tight_layout()

# graph_path = "graph.png"
# plt.savefig(graph_path)
# plt.close()

# ===== 1.3. Répartition des interventions par nacas ======
tmp_total = sum(data.values())
palette_naca = {
    0: "#6FCF97",
    1: "#27AE60",
    2: "#F2C94C",
    3: "#F2994A",
    4: "#E67E22",
    5: "#D62828",
    6: "#1D3557",
    7: "#000000",
    9: "#FFFFFF"
}
plt.figure()
plt.bar(data.keys(), data.values(), color=[
        palette_naca[int(k)] for k in data.keys()], edgecolor='black')
# print percentage on each bar
for i, v in enumerate(data.values()):
    pourcentage = (v / tmp_total) * 100
    plt.text(i, v + 2, f"{pourcentage:.2f}%", ha='center')
plt.title("Répartition interventions par naca")
plt.ylabel("Nombre d'interventions")
plt.tight_layout()

graph_path = "graph.png"
plt.savefig(graph_path)
plt.close()

# ====== 2. PDF ===========
# pdf_path = "output/rapport_priorites.pdf"
# doc = SimpleDocTemplate(pdf_path, pagesize=A4)
# elements = []

# styles = getSampleStyleSheet()

# elements.append(Paragraph("Rapport - Répartition des priorités", styles["Heading1"]))
# elements.append(Spacer(1, 0.5 * inch))
# elements.append(Image(graph_path, width=5*inch, height=3*inch))

# doc.build(elements)

# print("PDF généré :", pdf_path)
