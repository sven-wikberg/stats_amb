"""Tests des deux schémas de données pris en charge."""

import csv
from datetime import timedelta
import importlib.util
from pathlib import Path
import unittest

from ace_quality.loaders import DataFormatError, load_interventions
from tests.helpers import temporary_path


RAW_HEADERS = [
    "Date",
    "Statut",
    "Incohérences",
    "Période du jour",
    "Équipe",
    "Base",
    "Priorité à l'engagement",
    "Signaux prioritaires jusqu'au site",
    "Leader",
    "Équipier",
    "Véhicule",
    "Heure alarme",
    "Départ",
    "Arrivée sur site",
    "Départ du site",
    "Arrivée à destination",
    "Opérationnel",
    "Temps sur site",
    "Problème principal",
    "NACA",
    "Patient - Âge",
    "Prise en charge - Type d'adresse",
    "Prise en charge - Lieu",
    "Prise en charge - Localité",
    "Destination - Lieu",
    "Sans transport",
]

RAW_ROW = [
    "01.05.2026",
    "Contrôlé",
    "Non",
    "Jour",
    "Urgence",
    "ACENITON",
    "S1",
    "Oui",
    "Alice Exemple",
    "Bob Exemple",
    "ACE708",
    "23:30:00",
    "23:32:00",
    "23:50:00",
    "00:20:00",
    "00:35:00",
    "00:50:00",
    "00:30:00",
    "40 - Déficit neurologique",
    "4",
    "42",
    "1 - Domicile",
    "",
    "Genève",
    "Hôpital",
    "Non",
]


class LoaderTests(unittest.TestCase):
    """Contrôle le mapping sémantique et les cas de passage à minuit."""

    def _write_csv(self, path: Path, headers: list[str], row: list[str]) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(headers)
            writer.writerow(row)

    def test_new_raw_csv_is_normalized(self) -> None:
        path = temporary_path(self, "raw.csv")
        self._write_csv(path, RAW_HEADERS, RAW_ROW)

        records = load_interventions(path)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.priority, "S1 feux bleus")
        self.assertEqual(record.vehicle, "708")
        self.assertEqual(record.age, 42)
        self.assertEqual(record.naca, 4)
        self.assertEqual(record.on_site_duration, timedelta(minutes=30))

    def test_legacy_csv_remains_supported(self) -> None:
        path = temporary_path(self, "legacy.csv")
        headers = [f"Colonne {index}" for index in range(33)]
        row = [""] * 33
        row[0] = "01.05.2025"
        row[5] = "J2"
        row[6] = "P2"
        row[7] = "Alice Exemple"
        row[8] = "Bob Exemple"
        row[10] = "60704"
        row[15] = "23:50"
        row[16] = "00:20"
        row[24] = "1002 Douleur thoracique"
        row[26] = "3"
        row[32] = "65"
        self._write_csv(path, headers, row)

        record = load_interventions(path)[0]

        self.assertEqual(record.base, "Pierre-du-Niton")
        self.assertEqual(record.period_of_day, "Jour")
        self.assertEqual(record.vehicle, "704")
        self.assertEqual(record.on_site_duration, timedelta(minutes=30))

    def test_unknown_schema_is_rejected(self) -> None:
        path = temporary_path(self, "unknown.csv")
        self._write_csv(path, ["A", "B"], ["1", "2"])

        with self.assertRaisesRegex(DataFormatError, "non reconnu"):
            load_interventions(path)

    @unittest.skipUnless(
        importlib.util.find_spec("openpyxl"),
        "openpyxl n'est pas installé dans cet environnement",
    )
    def test_new_raw_xlsx_is_supported(self) -> None:
        # L'import reste local au test pour que les utilisateurs uniquement CSV
        # puissent exécuter les autres tests avant d'installer openpyxl.
        from openpyxl import Workbook

        path = temporary_path(self, "raw.xlsx")
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(RAW_HEADERS)
        worksheet.append(RAW_ROW)
        workbook.save(path)

        record = load_interventions(path)[0]

        self.assertEqual(record.priority, "S1 feux bleus")
        self.assertEqual(record.vehicle, "708")


if __name__ == "__main__":
    unittest.main()
