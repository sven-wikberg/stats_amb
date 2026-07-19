"""Composition du rapport PDF à partir des statistiques normalisées."""

from __future__ import annotations

from collections import Counter
from functools import partial
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from .analytics import ReportStats, display_name, format_duration
from .config import AppConfig


class NumberedHeaderCanvas(canvas.Canvas):
    """Ajoute un en-tête et un total de pages calculé après la mise en page."""

    def __init__(self, *args, header_text: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.header_text = header_text
        self._saved_page_states: list[dict] = []

    def showPage(self) -> None:  # noqa: N802 - nom imposé par ReportLab
        """Mémorise chaque page afin de connaître le total au moment de sauver."""

        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        """Rejoue les pages avec un compteur exact « Page X/Y »."""

        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_header(page_count)
            super().showPage()
        super().save()

    def _draw_header(self, page_count: int) -> None:
        """Dessine l'en-tête dans une zone réservée par la marge supérieure."""

        self.saveState()
        self.setFont("Helvetica-Bold", 9)
        self.drawString(2 * cm, 28.3 * cm, self.header_text)
        self.drawRightString(
            19 * cm, 28.3 * cm, f"Page {self._pageNumber}/{page_count}"
        )
        self.setStrokeColor(colors.HexColor("#3A506B"))
        self.line(2 * cm, 28 * cm, 19 * cm, 28 * cm)
        self.restoreState()


def _styles() -> dict[str, ParagraphStyle]:
    """Centralise la typographie pour conserver une hiérarchie cohérente."""

    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "AceTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=colors.HexColor("#1D3557"),
            spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "AceSection",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1D3557"),
            spaceAfter=8,
        ),
        "large": ParagraphStyle(
            "AceLarge",
            parent=base["BodyText"],
            fontSize=12.5,
            leading=17,
            spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "AceBody",
            parent=base["BodyText"],
            fontSize=10.5,
            leading=14,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "AceSmall",
            parent=base["BodyText"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#333333"),
        ),
    }


def _highlight(value: object) -> str:
    """Uniformise les chiffres clés rouges utilisés dans les paragraphes."""

    return f"<font color='#D62828'><b>{escape(str(value))}</b></font>"


def _image(path: Path, width: float = 15.2 * cm, height: float = 8.7 * cm) -> Image:
    """Crée des images de taille stable pour éviter les pages supplémentaires."""

    return Image(str(path), width=width, height=height)


def _top_people_text(counts: Counter[str]) -> str | None:
    """Produit la phrase de tête sans planter lorsque les noms sont absents."""

    if not counts:
        return None
    person, count = counts.most_common(1)[0]
    return (
        f"C'est <b>{escape(display_name(person))}</b> qui en a effectué le plus, "
        f"avec <b>{count}</b> interventions."
    )


def _top_pair_text(counts: Counter[tuple[str, str]]) -> str | None:
    """Décrit le binôme le plus fréquent avec des noms abrégés."""

    if not counts:
        return None
    pair, count = counts.most_common(1)[0]
    names = " et ".join(escape(display_name(person)) for person in pair)
    return f"Le binôme <b>{names}</b> arrive en tête avec <b>{count}</b> interventions."


def _ratio_list(title: str, ratios, limit: int = 3) -> str:
    """Crée une petite liste HTML de ratios par personne."""

    selected = list(ratios[:limit])
    if not selected:
        return title + "<br/>Données insuffisantes pour appliquer le seuil choisi."
    lines = [title]
    for index, metric in enumerate(selected, start=1):
        lines.append(
            f"{index}. <b>{metric.ratio:.1%}</b> pour "
            f"<b>{escape(display_name(metric.person))}</b> "
            f"({metric.matching}/{metric.total})"
        )
    return "<br/>".join(lines)


def _tied_people_sentence(people: dict[str, int], subject: str) -> str | None:
    """Gère une première place partagée sans supposer un seul gagnant."""

    if not people:
        return None
    names = ", ".join(escape(display_name(person)) for person in people)
    count = next(iter(people.values()))
    return f"<b>{names}</b> {subject}, avec <b>{count}</b> interventions."


def _quality_text(stats: ReportStats) -> str:
    """Expose la complétude du fichier au lieu de masquer les valeurs manquantes."""

    quality = stats.quality
    return (
        "<b>Contrôle des données sources</b><br/>"
        f"Lignes chargées : {quality.total_rows} ; "
        f"incohérences signalées : {quality.inconsistent_rows} ; "
        f"statuts annulés : {quality.cancelled_rows}.<br/>"
        f"Valeurs manquantes — priorité : {quality.missing_priority}, "
        f"NACA : {quality.missing_naca}, âge : {quality.missing_age}, "
        f"temps sur site : {quality.missing_on_site_duration}."
    )


def generate_report(
    config: AppConfig, stats: ReportStats, charts: dict[str, Path]
) -> Path:
    """Génère un rapport PDF paginé et retourne son chemin final."""

    config.output_dir.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    document = SimpleDocTemplate(
        str(config.report_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=1.5 * cm,
        title=f"Rapport qualité ACE - {config.period_label}",
        author="ACE",
    )
    elements = []

    # Page 1 — synthèse générale.
    elements.append(
        Paragraph(
            f"Rapport {escape(config.report_mode.capitalize())} - Interventions Ambulance<br/>"
            f"{escape(config.period_label)}",
            styles["title"],
        )
    )
    elements.append(Spacer(1, 0.25 * cm))
    elements.append(
        Paragraph(
            f"Sur la période, ACE a enregistré "
            f"{_highlight(stats.total_interventions)} interventions.",
            styles["large"],
        )
    )
    top_person = _top_people_text(stats.person_counts)
    if top_person:
        elements.append(Paragraph(top_person, styles["large"]))
    top_pair = _top_pair_text(stats.pair_counts)
    if top_pair:
        elements.append(Paragraph(top_pair, styles["large"]))

    elements.append(Spacer(1, 0.15 * cm))
    elements.append(Paragraph("Les problèmes principaux les plus fréquents :", styles["large"]))
    total_problems = sum(stats.problems.values())
    problem_lines = []
    for index, (problem, count) in enumerate(stats.problems.most_common(5), start=1):
        percentage = count / total_problems * 100 if total_problems else 0
        problem_lines.append(
            f"{index}. {escape(problem)} — <b>{percentage:.1f}%</b> ({count})"
        )
    elements.append(
        Paragraph(
            "<br/>".join(problem_lines) if problem_lines else "Données indisponibles.",
            styles["body"],
        )
    )
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(
        Paragraph(
            f"Le temps moyen passé sur site était de "
            f"{_highlight(format_duration(stats.average_on_site))}.",
            styles["large"],
        )
    )
    if stats.fastest_stroke is not None:
        case = stats.fastest_stroke
        date_text = case.intervention_date.strftime("%d.%m.%Y") if case.intervention_date else "date inconnue"
        elements.append(
            Paragraph(
                f"La prise en charge AVC explicitement identifiée la plus rapide a duré "
                f"{_highlight(format_duration(case.duration))}, par "
                f"<b>{escape(display_name(case.leader))}</b> et "
                f"<b>{escape(display_name(case.teammate))}</b>, le {date_text}.",
                styles["body"],
            )
        )
    else:
        elements.append(
            Paragraph(
                "L'indicateur AVC n'est pas affiché : le nouvel export de cette période "
                "ne contient pas de libellé identifiant un AVC avec certitude.",
                styles["small"],
            )
        )

    # Page 2 — priorités.
    elements.append(PageBreak())
    elements.append(Paragraph("Priorités des interventions", styles["section"]))
    elements.append(_image(charts["priorities"]))
    elements.append(Spacer(1, 0.25 * cm))
    if stats.p3_total:
        percentage = stats.p3_high_naca / stats.p3_total * 100
        elements.append(
            Paragraph(
                f"En <b><font color='#D62828'>P3</font></b>, "
                f"<b>{stats.p3_high_naca}</b> interventions sur <b>{stats.p3_total}</b> "
                f"ont été classées NACA 4+, soit <b>{percentage:.1f}%</b>.",
                styles["large"],
            )
        )
    else:
        elements.append(Paragraph("Aucune P3 exploitable sur la période.", styles["body"]))

    # Page 3 — NACA.
    elements.append(PageBreak())
    elements.append(Paragraph("NACA enregistrés", styles["section"]))
    elements.append(_image(charts["nacas"]))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(
        Paragraph(
            _ratio_list(
                "Trois personnes se démarquant par la proportion de NACA bas (0, 1, 9) :",
                stats.low_naca_people,
            ),
            styles["body"],
        )
    )
    elements.append(
        Paragraph(
            _ratio_list(
                "Trois personnes se démarquant par la proportion de NACA hauts (5, 6, 7) :",
                stats.high_naca_people,
            ),
            styles["body"],
        )
    )

    # Page 4 — âges.
    elements.append(PageBreak())
    elements.append(Paragraph("Âges des patients", styles["section"]))
    average_age_text = f"{stats.average_age:.1f} ans" if stats.average_age is not None else "indisponible"
    elements.append(
        Paragraph(
            f"L'âge moyen des patients était de {_highlight(average_age_text)}.",
            styles["large"],
        )
    )
    elements.append(_image(charts["ages"]))
    if stats.average_age_by_person:
        senior, senior_age = next(iter(stats.average_age_by_person.items()))
        junior, junior_age = next(reversed(stats.average_age_by_person.items()))
        elements.append(
            Paragraph(
                f"Les patients de <b>{escape(display_name(senior))}</b> avaient l'âge "
                f"moyen le plus élevé ({senior_age:.1f} ans), tandis que ceux de "
                f"<b>{escape(display_name(junior))}</b> avaient le plus faible "
                f"({junior_age:.1f} ans).",
                styles["body"],
            )
        )
    pediatric = _tied_people_sentence(
        stats.pediatric_leaders, "ont pris en charge le plus de patients de moins de 16 ans"
    )
    if pediatric:
        elements.append(Paragraph(pediatric, styles["body"]))

    # Page 5 — horaires.
    elements.append(PageBreak())
    elements.append(Paragraph("Heures d'intervention", styles["section"]))
    elements.append(_image(charts["hours"]))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(
        Paragraph(
            _ratio_list(
                "Trois personnes se démarquant entre 02 h et 06 h :",
                stats.night_people,
            ),
            styles["body"],
        )
    )
    noon = _tied_people_sentence(
        stats.noon_departure_leaders, "ont connu le plus de départs entre 12 h 00 et 12 h 59"
    )
    if noon:
        elements.append(Paragraph(noon, styles["body"]))

    # Page 6 — bases, ambulances et qualité de la source.
    elements.append(PageBreak())
    elements.append(Paragraph("Bases et ambulances", styles["section"]))
    elements.append(_image(charts["bases"], height=6.7 * cm))
    elements.append(Spacer(1, 0.1 * cm))
    elements.append(_image(charts["vehicles"], height=6.7 * cm))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(_quality_text(stats), styles["small"]))
    elements.append(Spacer(1, 0.1 * cm))
    elements.append(
        Paragraph(
            f"Pour les comparaisons par personne, seules les personnes disposant "
            f"d'au moins <b>{config.minimum_person_interventions}</b> observations "
            f"pour l'indicateur concerné ont été retenues.",
            styles["small"],
        )
    )

    header = (
        f"ACE - Rapport {config.report_mode.capitalize()} - {config.period_label}"
    )
    document.build(
        elements,
        canvasmaker=partial(NumberedHeaderCanvas, header_text=header),
    )
    return config.report_path
