"""Tests des indicateurs calculés sur le modèle normalisé."""

from datetime import date, time, timedelta
import unittest

from ace_quality.analytics import calculate_stats, display_name, format_duration
from ace_quality.models import Intervention


class AnalyticsTests(unittest.TestCase):
    """Vérifie les agrégations et les protections contre les valeurs absentes."""

    def test_core_metrics_and_data_quality(self) -> None:
        records = [
            Intervention(
                source_row=2,
                date=date(2026, 5, 1),
                status="Contrôlé",
                period_of_day="Jour",
                base="ACENITON",
                priority="P3",
                leader="Alice Exemple",
                teammate="Bob Exemple",
                vehicle="708",
                departure_at=time(12, 5),
                on_site_at=time(3, 15),
                on_site_duration=timedelta(minutes=30),
                problem="51 - Trauma des membres",
                naca=4,
                age=12,
            ),
            Intervention(
                source_row=3,
                status="Annulé",
                has_inconsistency=True,
                period_of_day="Nuit",
                base="ACENITON",
                priority="P1",
                leader="Alice Exemple",
                teammate="Bob Exemple",
                vehicle="708",
            ),
        ]

        stats = calculate_stats(records, minimum_person_interventions=1)

        self.assertEqual(stats.total_interventions, 2)
        self.assertEqual(stats.priorities["P3"], 1)
        self.assertEqual(stats.p3_total, 1)
        self.assertEqual(stats.p3_high_naca, 1)
        self.assertEqual(stats.person_counts["Alice Exemple"], 2)
        self.assertEqual(stats.pair_counts[("Alice Exemple", "Bob Exemple")], 2)
        self.assertEqual(stats.quality.inconsistent_rows, 1)
        self.assertEqual(stats.quality.cancelled_rows, 1)
        self.assertEqual(stats.quality.missing_age, 1)
        self.assertEqual(stats.average_on_site, timedelta(minutes=30))

    def test_empty_optional_values_do_not_crash(self) -> None:
        stats = calculate_stats([Intervention(source_row=2)], 10)

        self.assertIsNone(stats.average_age)
        self.assertIsNone(stats.average_on_site)
        self.assertEqual(stats.pediatric_leaders, {})
        self.assertEqual(stats.noon_departure_leaders, {})

    def test_display_helpers_accept_unusual_names_and_durations(self) -> None:
        self.assertEqual(display_name("Auxiliaire"), "Auxiliaire")
        self.assertEqual(display_name("Alice de l'Exemple"), "Alice L.")
        self.assertEqual(format_duration(timedelta(minutes=1)), "1 minute")
        self.assertEqual(format_duration(timedelta(minutes=75)), "1 h 15")


if __name__ == "__main__":
    unittest.main()
