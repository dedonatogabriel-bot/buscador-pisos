"""Test de humo: el repo tiene la estructura esperada y los paquetes importan."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_DIRS = [
    "scrapers/portales",
    "scrapers/inmobiliarias",
    "scrapers/fixtures",
    "enrich",
    "supabase/migrations",
    "supabase/functions",
    "apps-script",
    "web",
    "config",
    "docs",
    "legacy",
]


def test_expected_dirs_exist() -> None:
    missing = [d for d in EXPECTED_DIRS if not (ROOT / d).is_dir()]
    assert not missing, f"Faltan carpetas: {missing}"


def test_packages_import() -> None:
    import enrich
    import scrapers
    import scrapers.inmobiliarias
    import scrapers.portales

    assert scrapers and scrapers.portales and scrapers.inmobiliarias and enrich


def test_env_example_has_no_values() -> None:
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            name, _, value = line.partition("=")
            assert value == "", f"{name} tiene un valor en .env.example"
