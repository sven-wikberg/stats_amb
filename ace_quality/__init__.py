"""Génération des rapports qualité ACE à partir des exports opérationnels.

Le paquet contient la nouvelle chaîne de traitement. L'ancien code de ``stats.py``
reste présent pour conserver l'historique du projet, mais son point d'entrée
délègue désormais à cette implémentation testable et indépendante du format brut.
"""

from .config import AppConfig, ConfigError, load_config
from .loaders import DataFormatError, load_interventions

__all__ = [
    "AppConfig",
    "ConfigError",
    "DataFormatError",
    "load_config",
    "load_interventions",
]
