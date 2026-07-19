"""Création des graphiques du rapport avec un rendu non interactif."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

# Le backend Agg permet de générer des PNG sur un poste sans fenêtre graphique.
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .analytics import ReportStats


PRIORITY_COLORS = {
    "P1": "#D62828",
    "P2": "#F2C94C",
    "P3": "#27AE60",
    "S1 feux bleus": "#D62828",
    "S1 sans feux bleus": "#E67E22",
    "S1": "#E67E22",
    "S2": "#F2C94C",
}

NACA_COLORS = {
    0: "#6FCF97",
    1: "#27AE60",
    2: "#F2C94C",
    3: "#F2994A",
    4: "#E67E22",
    5: "#D62828",
    6: "#1D3557",
    7: "#000000",
    9: "#FFFFFF",
}

HOUR_COLORS = [
    "#0B132B", "#0B132B", "#1C2541", "#1C2541", "#3A506B", "#5BC0BE",
    "#89C2D9", "#A9D6E5", "#F1FAEE", "#FFE8A1", "#FFD166", "#FFC43D",
    "#FFB703", "#FFB703", "#FFD166", "#F4A261", "#E76F51", "#D62828",
    "#BC4749", "#6D597A", "#355070", "#1D3557", "#1D3557", "#0B132B",
]


def _annotate_bars(axis, values: list[int]) -> None:
    """Ajoute les pourcentages au-dessus des barres sans division par zéro."""

    total = sum(values)
    offset = max(values, default=0) * 0.02
    for index, value in enumerate(values):
        percentage = value / total * 100 if total else 0
        axis.text(index, value + offset, f"{percentage:.1f}%", ha="center", fontsize=8)


def _save_bar(
    counts: Counter,
    path: Path,
    title: str,
    xlabel: str,
    colors: list[str],
) -> None:
    """Génère un histogramme catégoriel standardisé et lisible dans le PDF."""

    labels = [str(label) for label in counts.keys()]
    values = list(counts.values())
    figure, axis = plt.subplots(figsize=(7, 4.2), layout="constrained")
    if values:
        axis.bar(labels, values, color=colors, edgecolor="black", linewidth=0.7)
        _annotate_bars(axis, values)
    else:
        axis.text(0.5, 0.5, "Données indisponibles", ha="center", va="center")
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel("Nombre d'interventions")
    axis.tick_params(axis="x", labelrotation=15)
    figure.savefig(path, dpi=220)
    plt.close(figure)


def _create_age_chart(stats: ReportStats, path: Path) -> None:
    """Utilise un histogramme robuste, y compris avec peu de valeurs d'âge."""

    figure, axis = plt.subplots(figsize=(7, 4.2), layout="constrained")
    if stats.ages:
        axis.hist(stats.ages, bins=range(0, 126, 5), color="#A9D6E5", edgecolor="white")
        if stats.average_age is not None:
            axis.axvline(
                stats.average_age,
                color="#D62828",
                linestyle="--",
                label=f"Âge moyen : {stats.average_age:.1f} ans",
            )
            axis.legend(loc="upper left")
    else:
        axis.text(0.5, 0.5, "Âges indisponibles", ha="center", va="center")
    axis.set_title("Distribution des âges des patients")
    axis.set_xlabel("Âge")
    axis.set_ylabel("Nombre de patients")
    figure.savefig(path, dpi=220)
    plt.close(figure)


def _create_hour_chart(stats: ReportStats, path: Path) -> None:
    """Affiche systématiquement les 24 heures, même lorsqu'une heure vaut zéro."""

    hours = list(range(24))
    values = [stats.interventions_by_hour[hour] for hour in hours]
    figure, axis = plt.subplots(figsize=(7, 4.2), layout="constrained")
    axis.bar(hours, values, color=HOUR_COLORS, edgecolor="black", linewidth=0.5)
    axis.set_xticks(hours, [f"{hour:02d}" for hour in hours], fontsize=7)
    axis.set_title("Nombre d'interventions par heure d'arrivée sur site")
    axis.set_xlabel("Heure")
    axis.set_ylabel("Nombre d'interventions")
    figure.savefig(path, dpi=220)
    plt.close(figure)


def _create_base_chart(
    stats: ReportStats, path: Path, base_labels: dict[str, str]
) -> None:
    """Construit les groupes depuis les bases réellement présentes dans l'export."""

    bases = sorted(stats.bases_by_period)
    day_values = [stats.bases_by_period[base].get("Jour", 0) for base in bases]
    night_values = [stats.bases_by_period[base].get("Nuit", 0) for base in bases]
    positions = list(range(len(bases)))
    width = 0.36

    figure, axis = plt.subplots(figsize=(7, 4.2), layout="constrained")
    if bases:
        day_bars = axis.bar(
            [position - width / 2 for position in positions],
            day_values,
            width,
            label="Jour",
            color="#FFE8A1",
            edgecolor="black",
        )
        night_bars = axis.bar(
            [position + width / 2 for position in positions],
            night_values,
            width,
            label="Nuit",
            color="#3A506B",
            edgecolor="black",
        )
        axis.bar_label(day_bars, padding=2, fontsize=8)
        axis.bar_label(night_bars, padding=2, fontsize=8)
        axis.set_xticks(
            positions,
            [base_labels.get(base, base) for base in bases],
            rotation=10,
        )
        axis.legend()
    else:
        axis.text(0.5, 0.5, "Bases indisponibles", ha="center", va="center")
    axis.set_title("Répartition des interventions par base")
    axis.set_ylabel("Nombre d'interventions")
    figure.savefig(path, dpi=220)
    plt.close(figure)


def create_charts(
    stats: ReportStats, graphs_dir: Path, base_labels: dict[str, str]
) -> dict[str, Path]:
    """Génère tous les PNG et retourne leurs chemins au constructeur PDF."""

    graphs_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "priorities": graphs_dir / "priorites.png",
        "vehicles": graphs_dir / "ambulances.png",
        "nacas": graphs_dir / "nacas.png",
        "ages": graphs_dir / "ages.png",
        "hours": graphs_dir / "interventions_par_heure.png",
        "bases": graphs_dir / "bases.png",
    }

    priority_order = [
        "P1", "P2", "P3", "S1 feux bleus", "S1 sans feux bleus", "S1", "S2"
    ]
    priorities = Counter(
        {key: stats.priorities[key] for key in priority_order if key in stats.priorities}
    )
    # Les éventuelles catégories futures restent visibles au lieu d'être perdues.
    priorities.update(
        {key: value for key, value in stats.priorities.items() if key not in priorities}
    )
    _save_bar(
        priorities,
        paths["priorities"],
        "Répartition des interventions par priorité",
        "Priorité",
        [PRIORITY_COLORS.get(key, "#457B9D") for key in priorities],
    )

    vehicles = Counter(dict(sorted(stats.vehicles.items())))
    vehicle_colors = ["#1D3557" if index % 2 == 0 else "#457B9D" for index in range(len(vehicles))]
    _save_bar(
        vehicles,
        paths["vehicles"],
        "Répartition des interventions par ambulance",
        "Ambulance",
        vehicle_colors,
    )

    naca_order = [0, 1, 2, 3, 4, 5, 6, 7, 9]
    nacas = Counter({naca: stats.nacas.get(naca, 0) for naca in naca_order})
    _save_bar(
        nacas,
        paths["nacas"],
        "Répartition des interventions par NACA",
        "NACA",
        [NACA_COLORS[naca] for naca in nacas],
    )

    _create_age_chart(stats, paths["ages"])
    _create_hour_chart(stats, paths["hours"])
    _create_base_chart(stats, paths["bases"], base_labels)
    return paths
