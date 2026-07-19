"""Modèles de données communs aux chargeurs et aux statistiques."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta


@dataclass(frozen=True, slots=True)
class Intervention:
    """Représentation normalisée d'une ligne d'intervention.

    Les deux formats pris en charge (ancien CSV de 33 colonnes et nouvel export
    Attrib de 174 colonnes) sont convertis vers ce modèle. Les calculs n'ont donc
    plus besoin de connaître les positions physiques des colonnes.
    """

    source_row: int
    date: date | None = None
    status: str = ""
    has_inconsistency: bool = False
    period_of_day: str = ""
    team: str = ""
    base: str = ""
    priority: str = ""
    leader: str = ""
    teammate: str = ""
    vehicle: str = ""
    alarm_at: time | None = None
    departure_at: time | None = None
    on_site_at: time | None = None
    depart_site_at: time | None = None
    arrival_destination_at: time | None = None
    operational_at: time | None = None
    on_site_duration: timedelta | None = None
    problem: str = ""
    naca: int | None = None
    age: int | None = None
    pickup_type: str = ""
    pickup_place: str = ""
    pickup_locality: str = ""
    destination_place: str = ""
    no_transport: bool = False


@dataclass(frozen=True, slots=True)
class DataQuality:
    """Compteurs de complétude affichés dans le rapport et dans la console."""

    total_rows: int
    inconsistent_rows: int
    cancelled_rows: int
    missing_priority: int
    missing_naca: int
    missing_age: int
    missing_on_site_duration: int
