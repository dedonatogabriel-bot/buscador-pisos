"""Carga y validación de config/busqueda.yaml."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config" / "busqueda.yaml"
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class ConfigError(ValueError):
    """La configuración no se pudo cargar o no es válida."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _check_hhmm(value: str) -> str:
    if not _HHMM.match(value):
        raise ValueError(f"hora inválida {value!r}, se espera HH:MM")
    return value


class HardFilters(_Strict):
    contract_type: Literal["traditional"]
    furnished: bool
    min_bedrooms: int = Field(ge=0)
    min_area_m2: int = Field(gt=0)
    require_balcony: bool
    require_heating: bool
    accepted_heating_types: list[str]
    min_floor: int = Field(ge=0)
    require_elevator: bool
    require_inside_isochrone: bool
    advertiser: list[Literal["owner", "agency"]] = Field(min_length=1)
    guarantee: str


class Budget(_Strict):
    currency: Literal["ARS", "USD"]
    max_rent: int = Field(gt=0)
    max_expenses: int = Field(ge=0)
    max_total: int = Field(gt=0)
    total_tolerance_pct: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def _total_covers_rent(self) -> Budget:
        if self.max_total < self.max_rent:
            raise ValueError("max_total no puede ser menor que max_rent")
        return self


class Indexation(_Strict):
    enabled: bool | None  # None = pendiente de confirmar por Marcos
    index: str
    frequency: Literal["monthly", "quarterly"]


class Neighborhoods(_Strict):
    accepted: list[str]
    vetoed: list[str]

    @model_validator(mode="after")
    def _no_overlap(self) -> Neighborhoods:
        both = {n.casefold() for n in self.accepted} & {n.casefold() for n in self.vetoed}
        if both:
            raise ValueError(f"barrios aceptados y vetados a la vez: {sorted(both)}")
        return self


class WorkPoint(_Strict):
    name: str


class Geography(_Strict):
    zone: str
    work_point: WorkPoint
    max_commute_minutes: int = Field(gt=0)
    preferred_subway_lines: list[str]


class ScoreWeights(_Strict):
    price: int = Field(ge=0)
    transport: int = Field(ge=0)
    space: int = Field(ge=0)
    comfort: int = Field(ge=0)
    urgency: int = Field(ge=0)
    environment: int = Field(ge=0)

    @model_validator(mode="after")
    def _sum_100(self) -> ScoreWeights:
        total = sum(self.model_dump().values())
        if total != 100:
            raise ValueError(f"los pesos del score deben sumar 100, suman {total}")
        return self


class TimeWindow(_Strict):
    start: str
    end: str

    _hhmm = field_validator("start", "end")(_check_hhmm)


class WeeklyReport(_Strict):
    weekday: Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    time: str

    _hhmm = field_validator("time")(_check_hhmm)


class Alerts(_Strict):
    timezone: str
    red_window: TimeWindow
    red_min_score: int = Field(ge=0, le=100)
    yellow_min_score: int = Field(ge=0, le=100)
    yellow_max_score: int = Field(ge=0, le=100)
    yellow_digest_times: list[str]
    weekly_market_report: WeeklyReport
    new_owner_listing_max_hours: int = Field(gt=0)

    @field_validator("timezone")
    @classmethod
    def _known_tz(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"zona horaria desconocida {value!r}") from exc
        return value

    @field_validator("yellow_digest_times")
    @classmethod
    def _digest_hhmm(cls, value: list[str]) -> list[str]:
        return [_check_hhmm(v) for v in value]

    @model_validator(mode="after")
    def _score_bands(self) -> Alerts:
        if self.yellow_min_score > self.yellow_max_score:
            raise ValueError("yellow_min_score no puede superar yellow_max_score")
        if self.yellow_max_score >= self.red_min_score:
            raise ValueError("la banda amarilla debe quedar por debajo de red_min_score")
        return self


class SearchConfig(_Strict):
    hard_filters: HardFilters
    budget: Budget
    indexation: Indexation
    neighborhoods: Neighborhoods
    geography: Geography
    score_weights: ScoreWeights
    alerts: Alerts
    target_move_in: dt.date


def format_errors(exc: ValidationError) -> str:
    lines = []
    for err in exc.errors():
        where = ".".join(str(p) for p in err["loc"]) or "<raíz>"
        lines.append(f"  - {where}: {err['msg']}")
    return "\n".join(lines)


def load_config(path: Path | str = DEFAULT_PATH) -> SearchConfig:
    """Lee y valida el YAML. Lanza ConfigError con un mensaje claro si algo está mal."""
    p = Path(path)
    try:
        raw: Any = yaml.safe_load(p.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"no existe el archivo de configuración: {p}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML inválido en {p}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{p}: se esperaba un mapa en la raíz")
    try:
        return SearchConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"configuración inválida en {p}:\n{format_errors(exc)}") from exc


def to_config_rows(cfg: SearchConfig) -> list[dict[str, Any]]:
    """Filas {key, value} (una por sección) para copiar a la tabla `config` de Supabase."""
    data = json.loads(cfg.model_dump_json())
    return [{"key": key, "value": value} for key, value in data.items()]
