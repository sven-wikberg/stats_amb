"""Petits utilitaires communs aux tests qui créent des fichiers locaux."""

from pathlib import Path
import unittest


TEST_TMP = Path(__file__).parent / "tmp"


def temporary_path(test_case: unittest.TestCase, filename: str) -> Path:
    """Réserve un fichier de test et garantit son nettoyage après le test."""

    path = TEST_TMP / filename
    if path.exists():
        path.unlink()
    test_case.addCleanup(path.unlink, missing_ok=True)
    return path
