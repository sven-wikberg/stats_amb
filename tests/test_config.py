"""Tests de la configuration externe TOML."""

from pathlib import Path
import unittest

from ace_quality.config import ConfigError, load_config
from tests.helpers import TEST_TMP, temporary_path


class ConfigTests(unittest.TestCase):
    """Vérifie les chemins relatifs et les erreurs de configuration courantes."""

    def test_relative_paths_are_resolved_from_config_file(self) -> None:
        data = temporary_path(self, "config-sample.csv")
        data.write_text("a;b\n1;2\n", encoding="utf-8")
        config_path = temporary_path(self, "config-relative.toml")
        config_path.write_text(
            """
[input]
path = "config-sample.csv"

[report]
period_label = "Mai 2026"
output_dir = "generated"
minimum_person_interventions = 5
""".strip(),
            encoding="utf-8",
        )

        config = load_config(config_path)

        self.assertEqual(config.input_path, data.resolve())
        self.assertEqual(config.output_dir, (TEST_TMP / "generated").resolve())
        self.assertEqual(config.minimum_person_interventions, 5)
        self.assertTrue(config.report_filename.endswith(".pdf"))

    def test_missing_input_file_has_an_explicit_error(self) -> None:
        config_path = temporary_path(self, "config-missing.toml")
        config_path.write_text(
            "[input]\npath='missing.csv'\n[report]\nperiod_label='Mai 2026'\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ConfigError, "introuvable"):
            load_config(config_path)


if __name__ == "__main__":
    unittest.main()
