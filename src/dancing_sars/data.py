"""Deterministic synthetic observations for the surface-change demo."""

from __future__ import annotations

import math
from datetime import date

from .studies import STUDY_BY_ID, StudyArea


OBSERVATION_DATES = (
    date(2022, 1, 1),
    date(2022, 4, 1),
    date(2022, 7, 1),
    date(2022, 10, 1),
    date(2023, 1, 1),
    date(2023, 4, 1),
    date(2023, 7, 1),
    date(2023, 10, 1),
    date(2024, 1, 1),
    date(2024, 4, 1),
    date(2024, 7, 1),
    date(2024, 10, 1),
    date(2025, 1, 1),
)

_START_DATE = OBSERVATION_DATES[0]
_GRID_WIDTH = 9
_GRID_HEIGHT = 7
_DAYS_PER_YEAR = 365.25
_METERS_PER_DEG_LAT = 111_320


def get_study(study_id: str) -> StudyArea:
    try:
        return STUDY_BY_ID[study_id]
    except KeyError as error:
        raise ValueError(f"Unknown study area: {study_id}") from error


def _sample_points(study: StudyArea) -> list[dict[str, float | str]]:
    points: list[dict[str, float | str]] = []
    for row in range(_GRID_HEIGHT):
        for col in range(_GRID_WIDTH):
            dx = col - (_GRID_WIDTH - 1) / 2
            dy = row - (_GRID_HEIGHT - 1) / 2
            hotspot = math.exp(-(((dx + 1.2) / 3.0) ** 2 + ((dy - 0.2) / 2.5) ** 2))
            ripple = math.sin(col * 1.7 + row * 0.9) * study.ripple_m_year
            velocity = max(
                0.0,
                study.velocity_base_m_year + hotspot * study.velocity_peak_m_year + ripple,
            )
            heading = study.heading_deg + math.sin(row * 0.53 + col * 0.14) * study.heading_variation_deg
            points.append(
                {
                    "sample_id": f"{study.id_prefix}-{row * _GRID_WIDTH + col + 1:03d}",
                    "base_lon": study.longitude + dx * study.grid_lon_step + dy * study.grid_lon_step * 0.1,
                    "base_lat": study.latitude + dy * study.grid_lat_step + dx * study.grid_lat_step * 0.06,
                    "velocity_m_year": velocity,
                    "heading_deg": heading,
                }
            )
    return points


def _rate_label(velocity_m_year: float) -> str:
    if velocity_m_year < 1:
        return f"{velocity_m_year * 100:.2f} cm/yr"
    return f"{velocity_m_year:.0f} m/yr"


def _distance_label(distance_m: float) -> str:
    if distance_m < 0.1:
        return f"{distance_m * 1000:.1f} mm"
    if distance_m < 1:
        return f"{distance_m * 100:.1f} cm"
    return f"{distance_m:,.1f} m"


def build_observation(
    observation_date: date, study_id: str = "jakobshavn"
) -> list[dict[str, float | str | list[list[float]] | list[int]]]:
    """Build one simulated acquisition for a study area and date."""
    study = get_study(study_id)
    elapsed_years = (observation_date - _START_DATE).days / _DAYS_PER_YEAR
    samples = _sample_points(study)
    result: list[dict[str, float | str | list[list[float]] | list[int]]] = []

    for sample in samples:
        velocity = float(sample["velocity_m_year"])
        distance_m = velocity * elapsed_years
        heading_rad = math.radians(float(sample["heading_deg"]))
        east_m = math.sin(heading_rad) * distance_m
        north_m = math.cos(heading_rad) * distance_m
        latitude = float(sample["base_lat"])
        longitude = float(sample["base_lon"])
        current_lat = latitude + north_m / _METERS_PER_DEG_LAT
        meters_per_degree_lon = _METERS_PER_DEG_LAT * math.cos(math.radians(latitude))
        current_lon = longitude + east_m / meters_per_degree_lon

        # This display multiplier makes tiny modeled motion visible at map scale.
        display_lat = latitude + (current_lat - latitude) * study.display_scale
        display_lon = longitude + (current_lon - longitude) * study.display_scale
        normalized = min(1.0, velocity / max(0.000001, study.velocity_base_m_year + study.velocity_peak_m_year))
        color = [255, 164, 84, 220] if normalized >= 0.58 else [57, 204, 201, 215]
        result.append(
            {
                "sample_id": str(sample["sample_id"]),
                "lon": display_lon,
                "lat": display_lat,
                "base_lon": longitude,
                "base_lat": latitude,
                "velocity_m_year": round(velocity, 6),
                "velocity_label": _rate_label(velocity),
                "displacement_m": round(distance_m, 6),
                "displacement_label": _distance_label(distance_m),
                "heading_deg": round(float(sample["heading_deg"]), 1),
                "path": [[longitude, latitude], [display_lon, display_lat]],
                "color": color,
                "radius_m": 200 + normalized * 500,
            }
        )
    return result


def build_timeseries(study_id: str = "jakobshavn") -> list[dict[str, date | float]]:
    """Return mean cumulative displacement for every synthetic acquisition."""
    get_study(study_id)
    series: list[dict[str, date | float]] = []
    for observation_date in OBSERVATION_DATES:
        points = build_observation(observation_date, study_id)
        displacements = [float(point["displacement_m"]) for point in points]
        velocities = sorted(float(point["velocity_m_year"]) for point in points)
        series.append(
            {
                "date": observation_date,
                "mean_displacement_m": round(sum(displacements) / len(displacements), 6),
                "median_velocity_m_year": round(velocities[len(velocities) // 2], 6),
            }
        )
    return series
