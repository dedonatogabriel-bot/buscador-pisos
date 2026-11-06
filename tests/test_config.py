from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from enrich.config import DEFAULT_PATH, ConfigError, load_config, to_config_rows


def _write(tmp_path: Path, mutate: Callable[[dict[str, Any]], None] | None = None) -> Path:
    data = yaml.safe_load(DEFAULT_PATH.read_text(encoding="utf-8"))
    if mutate:
        mutate(data)
    out = tmp_path / "busqueda.yaml"
    out.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return out


def test_default_config_loads() -> None:
    cfg = load_config()
    assert cfg.budget.max_total == 900_000
    assert cfg.budget.currency == "ARS"
    assert cfg.hard_filters.min_area_m2 == 45
    assert sum(cfg.score_weights.model_dump().values()) == 100
    assert cfg.indexation.enabled is True
    assert cfg.indexation.index == "IPC"
    assert cfg.budget.max_expenses is None
    assert cfg.hard_filters.accepted_heating_types == ["any"]
    assert len(cfg.neighborhoods.accepted) == 38
    assert {"Almagro", "Barracas"} <= set(cfg.neighborhoods.accepted)
    assert not {"Constitución", "La Boca"} & set(cfg.neighborhoods.accepted)
    assert cfg.neighborhoods.vetoed == []


def test_rows_for_config_table() -> None:
    rows = to_config_rows(load_config())
    keys = {r["key"] for r in rows}
    assert {"budget", "score_weights", "alerts", "target_move_in"} <= keys
    assert next(r for r in rows if r["key"] == "target_move_in")["value"] == "2027-05-01"


def test_weights_must_sum_100(tmp_path: Path) -> None:
    path = _write(tmp_path, lambda d: d["score_weights"].update(price=40))
    with pytest.raises(ConfigError, match=r"score_weights.*sumar 100, suman 105"):
        load_config(path)


def test_negative_budget_is_clear_error(tmp_path: Path) -> None:
    path = _write(tmp_path, lambda d: d["budget"].update(max_rent=-1))
    with pytest.raises(ConfigError, match=r"budget\.max_rent"):
        load_config(path)


def test_bad_hour(tmp_path: Path) -> None:
    path = _write(tmp_path, lambda d: d["alerts"]["red_window"].update(start="8am"))
    with pytest.raises(ConfigError, match="HH:MM"):
        load_config(path)


def test_unknown_key_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, lambda d: d["budget"].update(tope=1))
    with pytest.raises(ConfigError, match=r"budget\.tope"):
        load_config(path)


def test_neighborhood_in_both_lists(tmp_path: Path) -> None:
    def mutate(d: dict[str, Any]) -> None:
        d["neighborhoods"] = {"accepted": ["Almagro"], "vetoed": ["almagro"]}

    with pytest.raises(ConfigError, match="aceptados y vetados"):
        load_config(_write(tmp_path, mutate))


def test_yellow_band_below_red(tmp_path: Path) -> None:
    path = _write(tmp_path, lambda d: d["alerts"].update(yellow_max_score=85))
    with pytest.raises(ConfigError, match="red_min_score"):
        load_config(path)


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="no existe"):
        load_config(tmp_path / "nada.yaml")
