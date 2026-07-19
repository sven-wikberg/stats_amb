"""Interface en ligne de commande du générateur de rapports."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import sys

from .analytics import calculate_stats
from .config import ConfigError, load_config
from .loaders import DataFormatError, load_interventions


def _parser() -> argparse.ArgumentParser:
    """Déclare les options sans dupliquer les valeurs métier de config.toml."""

    parser = argparse.ArgumentParser(
        description="Génère le rapport qualité ACE depuis un export CSV ou XLSX."
    )
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Chemin du fichier TOML (défaut : config.toml).",
    )
    parser.add_argument(
        "--input",
        help="Remplace temporairement input.path sans modifier config.toml.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Valide et résume le fichier sans générer de graphiques ni de PDF.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Exécute la chaîne complète avec des messages d'erreur actionnables."""

    args = _parser().parse_args(argv)
    try:
        config = load_config(args.config)
        if args.input:
            override = Path(args.input).resolve()
            if not override.exists():
                raise ConfigError(f"Fichier de données introuvable : {override}")
            config = replace(config, input_path=override)

        print(f"Lecture des données : {config.input_path}")
        interventions = load_interventions(config.input_path, config.delimiter)
        stats = calculate_stats(
            interventions, config.minimum_person_interventions
        )
        quality = stats.quality
        print(
            f"{quality.total_rows} interventions chargées ; "
            f"{quality.inconsistent_rows} incohérence(s) signalée(s) ; "
            f"{quality.missing_naca} NACA manquant(s)."
        )

        if args.validate_only:
            print("Validation terminée : aucun fichier n'a été généré.")
            return 0

        # Les dépendances graphiques ne sont importées qu'au moment où elles
        # sont nécessaires ; la validation des données reste ainsi légère.
        from .charts import create_charts
        from .report import generate_report

        charts = create_charts(stats, config.graphs_dir, config.base_labels)
        report_path = generate_report(config, stats, charts)
        print(f"Rapport généré : {report_path}")
        return 0
    except (ConfigError, DataFormatError, OSError, ValueError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
