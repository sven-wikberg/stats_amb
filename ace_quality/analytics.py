"""Calculs statistiques indépendants du format d'entrée et du rendu PDF."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from statistics import mean
from typing import Iterable

from .models import DataQuality, Intervention


@dataclass(frozen=True, slots=True)
class PersonRatio:
    """Ratio calculé pour une personne après application du seuil d'activité."""

    person: str
    total: int
    matching: int

    @property
    def ratio(self) -> float:
        return self.matching / self.total if self.total else 0.0


@dataclass(frozen=True, slots=True)
class FastCase:
    """Intervention temporelle remarquable, si les données la rendent certaine."""

    duration: timedelta
    leader: str
    teammate: str
    intervention_date: date | None


@dataclass(frozen=True, slots=True)
class ReportStats:
    """Ensemble des résultats nécessaires aux graphiques et au rapport."""

    total_interventions: int
    priorities: Counter[str]
    vehicles: Counter[str]
    nacas: Counter[int]
    problems: Counter[str]
    ages: tuple[int, ...]
    average_age: float | None
    average_on_site: timedelta | None
    interventions_by_hour: Counter[int]
    bases_by_period: dict[str, Counter[str]]
    person_counts: Counter[str]
    pair_counts: Counter[tuple[str, str]]
    low_naca_people: tuple[PersonRatio, ...]
    high_naca_people: tuple[PersonRatio, ...]
    night_people: tuple[PersonRatio, ...]
    average_age_by_person: dict[str, float]
    pediatric_leaders: dict[str, int]
    noon_departure_leaders: dict[str, int]
    p3_total: int
    p3_high_naca: int
    fastest_stroke: FastCase | None
    quality: DataQuality


def _clean_person(value: str) -> str:
    """Évite qu'un double espace crée deux identités statistiques différentes."""

    return " ".join(value.split())


def display_name(value: str) -> str:
    """Abrège un nom sans supposer qu'il contient exactement deux mots."""

    parts = _clean_person(value).split()
    if len(parts) < 2:
        return parts[0] if parts else "Inconnu"
    # Une particule finale ou un nom saisi en minuscules doit malgré tout produire
    # une initiale homogène dans le rapport (par exemple « Alice L. »).
    return f"{parts[0]} {parts[-1][0].upper()}."


def format_duration(value: timedelta | None) -> str:
    """Formate une durée lisible et gère proprement l'absence de valeur."""

    if value is None:
        return "indisponible"
    total_minutes = int(round(value.total_seconds() / 60))
    hours, minutes = divmod(total_minutes, 60)
    if hours == 0:
        return "1 minute" if minutes == 1 else f"{minutes} minutes"
    if minutes == 0:
        return "1 heure" if hours == 1 else f"{hours} heures"
    return f"{hours} h {minutes:02d}"


def _time_delta(start: time | None, end: time | None) -> timedelta | None:
    """Calcule un délai en tenant compte d'un éventuel passage à minuit."""

    if start is None or end is None:
        return None
    reference = date(2000, 1, 1)
    start_dt = datetime.combine(reference, start)
    end_dt = datetime.combine(reference, end)
    if end_dt < start_dt:
        end_dt += timedelta(days=1)
    return end_dt - start_dt


def _top_ties(counts: Counter[str]) -> dict[str, int]:
    """Conserve toutes les personnes à égalité pour la première place."""

    if not counts:
        return {}
    maximum = max(counts.values())
    return {person: count for person, count in counts.items() if count == maximum}


def _person_ratios(
    values: dict[str, list[object]],
    predicate,
    minimum_interventions: int,
) -> tuple[PersonRatio, ...]:
    """Calcule puis trie un ratio, en filtrant les petits échantillons."""

    ratios = []
    for person, person_values in values.items():
        total = len(person_values)
        if total < minimum_interventions:
            continue
        matching = sum(1 for value in person_values if predicate(value))
        ratios.append(PersonRatio(person=person, total=total, matching=matching))
    return tuple(sorted(ratios, key=lambda item: (item.ratio, item.matching), reverse=True))


def calculate_stats(
    interventions: Iterable[Intervention], minimum_person_interventions: int
) -> ReportStats:
    """Calcule tous les indicateurs en un seul passage sur les interventions."""

    records = list(interventions)
    priorities: Counter[str] = Counter()
    vehicles: Counter[str] = Counter()
    nacas: Counter[int] = Counter()
    problems: Counter[str] = Counter()
    interventions_by_hour: Counter[int] = Counter({hour: 0 for hour in range(24)})
    bases_by_period: dict[str, Counter[str]] = defaultdict(Counter)
    person_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()

    naca_by_person: dict[str, list[object]] = defaultdict(list)
    night_by_person: dict[str, list[object]] = defaultdict(list)
    ages_by_person: dict[str, list[int]] = defaultdict(list)
    pediatric_counts: Counter[str] = Counter()
    noon_counts: Counter[str] = Counter()

    ages: list[int] = []
    on_site_durations: list[timedelta] = []
    p3_total = 0
    p3_high_naca = 0
    fastest_stroke: FastCase | None = None

    for record in records:
        if record.priority:
            priorities[record.priority] += 1
        if record.vehicle:
            vehicles[record.vehicle] += 1
        if record.naca is not None:
            nacas[record.naca] += 1
        if record.problem and not record.problem.startswith("0000"):
            problems[record.problem] += 1
        if record.age is not None:
            ages.append(record.age)
        if record.on_site_duration is not None:
            on_site_durations.append(record.on_site_duration)
        if record.on_site_at is not None:
            interventions_by_hour[record.on_site_at.hour] += 1

        period = record.period_of_day or "Non renseigné"
        base = record.base or "Non renseignée"
        bases_by_period[base][period] += 1

        people = tuple(
            person
            for person in (_clean_person(record.leader), _clean_person(record.teammate))
            if person
        )
        for person in people:
            person_counts[person] += 1
            if record.naca is not None:
                naca_by_person[person].append(record.naca)
            if record.on_site_at is not None:
                is_night = 2 <= record.on_site_at.hour < 6
                night_by_person[person].append(is_night)
            if record.age is not None:
                ages_by_person[person].append(record.age)
                if record.age < 16:
                    pediatric_counts[person] += 1
            if record.departure_at is not None and record.departure_at.hour == 12:
                noon_counts[person] += 1

        if len(people) == 2 and people[0] != people[1]:
            pair_counts[tuple(sorted(people, key=str.casefold))] += 1

        if record.priority == "P3" and record.naca is not None:
            p3_total += 1
            if record.naca >= 4:
                p3_high_naca += 1

        # Le nouveau format ne contient pas de champ AVC dédié. On ne retient
        # donc que les libellés explicitement AVC/vasculaires, sans extrapoler
        # depuis le code générique « déficit neurologique ».
        problem_lower = record.problem.casefold()
        is_explicit_stroke = "avc" in problem_lower or "vasculaire" in problem_lower
        if is_explicit_stroke:
            duration = _time_delta(record.alarm_at, record.arrival_destination_at)
            if duration is not None and (
                fastest_stroke is None or duration < fastest_stroke.duration
            ):
                fastest_stroke = FastCase(
                    duration=duration,
                    leader=record.leader,
                    teammate=record.teammate,
                    intervention_date=record.date,
                )

    low_naca_people = _person_ratios(
        naca_by_person,
        lambda value: value in {0, 1, 9},
        minimum_person_interventions,
    )
    high_naca_people = _person_ratios(
        naca_by_person,
        lambda value: value in {5, 6, 7},
        minimum_person_interventions,
    )
    night_people = _person_ratios(
        night_by_person,
        bool,
        minimum_person_interventions,
    )

    average_age_by_person = {
        person: mean(person_ages)
        for person, person_ages in ages_by_person.items()
        if len(person_ages) >= minimum_person_interventions
    }

    quality = DataQuality(
        total_rows=len(records),
        inconsistent_rows=sum(record.has_inconsistency for record in records),
        cancelled_rows=sum("annul" in record.status.casefold() for record in records),
        missing_priority=sum(not record.priority for record in records),
        missing_naca=sum(record.naca is None for record in records),
        missing_age=sum(record.age is None for record in records),
        missing_on_site_duration=sum(
            record.on_site_duration is None for record in records
        ),
    )

    return ReportStats(
        total_interventions=len(records),
        priorities=priorities,
        vehicles=vehicles,
        nacas=nacas,
        problems=problems,
        ages=tuple(ages),
        average_age=mean(ages) if ages else None,
        average_on_site=(
            timedelta(
                seconds=mean(duration.total_seconds() for duration in on_site_durations)
            )
            if on_site_durations
            else None
        ),
        interventions_by_hour=interventions_by_hour,
        bases_by_period=dict(bases_by_period),
        person_counts=person_counts,
        pair_counts=pair_counts,
        low_naca_people=low_naca_people,
        high_naca_people=high_naca_people,
        night_people=night_people,
        average_age_by_person=dict(
            sorted(average_age_by_person.items(), key=lambda item: item[1], reverse=True)
        ),
        pediatric_leaders=_top_ties(pediatric_counts),
        noon_departure_leaders=_top_ties(noon_counts),
        p3_total=p3_total,
        p3_high_naca=p3_high_naca,
        fastest_stroke=fastest_stroke,
        quality=quality,
    )
