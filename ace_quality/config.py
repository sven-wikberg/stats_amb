"""Lecture et validation de la configuration TOML du programme."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import tomllib


class ConfigError(ValueError):
    """Erreur de configuration présentée à l'utilisateur sans trace technique."""


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Configuration résolue, avec des chemins absolus prêts à être utilisés."""

    input_path: Path
    output_dir: Path
    report_filename: str
    period_label: str
    report_mode: str
    minimum_person_interventions: int
    delimiter: str = ";"
    base_labels: dict[str, str] = field(default_factory=dict)

    @property
    def report_path(self) -> Path:
        """Retourne le chemin final du PDF."""

        return self.output_dir / self.report_filename

    @property
    def graphs_dir(self) -> Path:
        """Isole les graphiques intermédiaires des rapports finaux."""

        return self.output_dir / "graphs"


def _resolve_from_config(config_path: Path, value: str, field_name: str) -> Path:
    """Résout un chemin relatif par rapport au fichier TOML, pas au terminal."""

    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Le champ '{field_name}' doit contenir un chemin.")
    path = Path(value.strip())
    if not path.is_absolute():
        path = config_path.parent / path
    return path.resolve()


def _default_report_filename(period_label: str) -> str:
    """Crée un nom portable tout en conservant les accents lisibles."""

    safe_label = re.sub(r'[<>:"/\\|?*]+', "-", period_label).strip(" .-")
    return f"rapport_qualite - {safe_label.lower()}.pdf"


def load_config(path: str | Path = "config.toml") -> AppConfig:
    """Charge ``config.toml`` et produit des erreurs explicites si nécessaire."""

    config_path = Path(path).resolve()
    if not config_path.exists():
        raise ConfigError(f"Fichier de configuration introuvable : {config_path}")

    try:
        with config_path.open("rb") as handle:
            raw = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Configuration TOML invalide : {exc}") from exc

    input_section = raw.get("input", {})
    report_section = raw.get("report", {})
    base_labels = raw.get("base_labels", {})

    input_path = _resolve_from_config(
        config_path, input_section.get("path", ""), "input.path"
    )
    if not input_path.exists():
        raise ConfigError(f"Fichier de données introuvable : {input_path}")

    output_dir = _resolve_from_config(
        config_path, report_section.get("output_dir", "output"), "report.output_dir"
    )
    period_label = str(report_section.get("period_label", "")).strip()
    if not period_label:
        raise ConfigError("Le champ 'report.period_label' est obligatoire.")

    report_mode = str(report_section.get("mode", "mensuel")).strip().lower()
    if report_mode not in {"mensuel", "annuel"}:
        raise ConfigError("Le champ 'report.mode' doit valoir 'mensuel' ou 'annuel'.")

    minimum = report_section.get(
        "minimum_person_interventions", 100 if report_mode == "annuel" else 10
    )
    if not isinstance(minimum, int) or minimum < 1:
        raise ConfigError(
            "Le champ 'report.minimum_person_interventions' doit être un entier positif."
        )

    delimiter = str(input_section.get("delimiter", ";"))
    if len(delimiter) != 1:
        raise ConfigError("Le séparateur CSV doit contenir exactement un caractère.")

    filename = str(report_section.get("filename", "")).strip()
    if not filename:
        filename = _default_report_filename(period_label)
    if Path(filename).name != filename or not filename.lower().endswith(".pdf"):
        raise ConfigError("Le nom du rapport doit être un simple nom de fichier .pdf.")

    if not isinstance(base_labels, dict):
        raise ConfigError("La section 'base_labels' doit être une table TOML.")

    return AppConfig(
        input_path=input_path,
        output_dir=output_dir,
        report_filename=filename,
        period_label=period_label,
        report_mode=report_mode,
        minimum_person_interventions=minimum,
        delimiter=delimiter,
        base_labels={str(key): str(value) for key, value in base_labels.items()},
    )
