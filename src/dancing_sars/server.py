"""FastAPI JSON API with a Flask-rendered web interface mounted at the root."""

from __future__ import annotations

import csv
from datetime import date
from io import StringIO
from typing import Literal

from a2wsgi import WSGIMiddleware
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from flask import Flask, render_template

from .data import OBSERVATION_DATES, build_observation, build_timeseries, get_study
from .map_layers import build_deck
from .studies import STUDY_AREAS


flask_app = Flask(__name__, template_folder="templates", static_folder="static")
app = FastAPI(
    title="Dancing with the SARs API",
    description="Local JSON and map endpoints for the synthetic surface-change visualizer.",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)


@flask_app.get("/")
def home():
    return render_template("index.html")


def _study_or_404(study_id: str):
    try:
        return get_study(study_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def _date_or_404(index: int) -> date:
    if index < 0 or index >= len(OBSERVATION_DATES):
        raise HTTPException(status_code=404, detail="Observation index is outside this timeline.")
    return OBSERVATION_DATES[index]


@app.get("/api/health", tags=["status"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "dancing-with-the-sars"}


@app.get("/api/studies", tags=["studies"])
def list_studies() -> list[dict[str, str | float]]:
    return [study.public_dict() for study in STUDY_AREAS]


@app.get("/api/studies/{study_id}/history", tags=["observations"])
def study_history(study_id: str) -> list[dict[str, str | float]]:
    _study_or_404(study_id)
    return [
        {
            "date": point["date"].isoformat(),
            "mean_displacement_m": point["mean_displacement_m"],
            "median_velocity_m_year": point["median_velocity_m_year"],
        }
        for point in build_timeseries(study_id)
    ]


@app.get("/api/studies/{study_id}/observations/{index}", tags=["observations"])
def observation(study_id: str, index: int) -> dict[str, object]:
    study = _study_or_404(study_id)
    observed_date = _date_or_404(index)
    previous_date = OBSERVATION_DATES[max(0, index - 1)]
    records = build_observation(observed_date, study_id)
    velocities = sorted(float(point["velocity_m_year"]) for point in records)
    mean_displacement = sum(float(point["displacement_m"]) for point in records) / len(records)
    return {
        "study": study.public_dict(),
        "date": observed_date.isoformat(),
        "previous_date": previous_date.isoformat(),
        "interval_days": (observed_date - previous_date).days if index else 0,
        "median_velocity_m_year": velocities[len(velocities) // 2],
        "mean_displacement_m": mean_displacement,
        "sample_count": len(records),
        "records": records,
        "simulated": True,
    }


@app.get("/api/studies/{study_id}/observations/{index}/map", response_class=HTMLResponse, tags=["map"])
def observation_map(
    study_id: str,
    index: int,
    vectors: bool = True,
    footprint: bool = True,
    theme: Literal["dark", "light"] = Query(default="dark"),
    nasa_imagery: bool = True,
) -> HTMLResponse:
    study = _study_or_404(study_id)
    observed_date = _date_or_404(index)
    records = build_observation(observed_date, study_id)
    deck = build_deck(
        records,
        study,
        vectors,
        footprint,
        map_style=theme,
        observation_date=observed_date,
        show_nasa_imagery=nasa_imagery,
    )
    return HTMLResponse(deck.to_html(as_string=True, iframe_height=530))


@app.get("/api/studies/{study_id}/observations/{index}/csv", tags=["exports"])
def observation_csv(study_id: str, index: int) -> Response:
    _study_or_404(study_id)
    observed_date = _date_or_404(index)
    records = build_observation(observed_date, study_id)
    fields = [
        "sample_id",
        "lon",
        "lat",
        "base_lon",
        "base_lat",
        "velocity_m_year",
        "displacement_m",
        "heading_deg",
    ]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    filename = f"{study_id}-synthetic-{observed_date.isoformat()}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# Keep API routes above the catch-all mount so /api requests stay in FastAPI.
app.mount("/", WSGIMiddleware(flask_app), name="flask-ui")
