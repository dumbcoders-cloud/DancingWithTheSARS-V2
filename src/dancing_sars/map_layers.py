"""PyDeck layer construction for NASA imagery and synthetic study-area scenes."""

from __future__ import annotations

from datetime import date
from typing import Any

import pydeck as pdk


def _footprint(study: Any) -> dict[str, Any]:
    half_lon = study.grid_lon_step * 4.8
    half_lat = study.grid_lat_step * 3.8
    west, east = study.longitude - half_lon, study.longitude + half_lon
    south, north = study.latitude - half_lat, study.latitude + half_lat
    return {
        "type": "Feature",
        "properties": {"name": f"Synthetic footprint · {study.name}"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
        },
    }


def build_deck(
    records: list[dict[str, Any]],
    study: Any,
    show_vectors: bool,
    show_footprint: bool,
    map_style: str = "dark",
    observation_date: date | None = None,
    show_nasa_imagery: bool = True,
) -> pdk.Deck:
    layers: list[pdk.Layer] = []

    if show_nasa_imagery and observation_date is not None:
        date_text = observation_date.isoformat()
        tile_url = (
            "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
            "MODIS_Terra_CorrectedReflectance_TrueColor/default/"
            f"{date_text}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"
        )
        layers.append(
            pdk.Layer(
                "TileLayer",
                data=tile_url,
                id=f"nasa-modis-terra-{date_text}",
                min_zoom=0,
                max_zoom=9,
                tile_size=256,
                opacity=0.92,
                pickable=False,
                render_sub_layers=(
                    "props => { const {west, south, east, north} = props.tile.bbox; "
                    "return new deck.BitmapLayer(props, {data: null, image: props.data, "
                    "bounds: [west, south, east, north]}); }"
                ),
            )
        )

    if show_footprint:
        layers.append(
            pdk.Layer(
                "GeoJsonLayer",
                data=_footprint(study),
                stroked=True,
                filled=True,
                get_fill_color=[57, 204, 201, 18],
                get_line_color=[91, 220, 211, 180],
                get_line_width=2,
                line_width_min_pixels=1,
                pickable=True,
            )
        )

    if show_vectors:
        layers.append(
            pdk.Layer(
                "PathLayer",
                data=records,
                get_path="path",
                get_color=[245, 174, 104, 145],
                get_width=2,
                width_min_pixels=1,
                width_units="pixels",
                pickable=True,
            )
        )

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=records,
            get_position="[lon, lat]",
            get_fill_color="color",
            get_radius="radius_m",
            radius_units="meters",
            radius_min_pixels=4,
            radius_max_pixels=13,
            line_width_min_pixels=1,
            stroked=True,
            get_line_color=[10, 20, 28, 220],
            pickable=True,
            auto_highlight=True,
        )
    )

    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=study.latitude,
            longitude=study.longitude,
            zoom=study.zoom,
            pitch=18,
            bearing=-8,
        ),
        map_provider="carto",
        map_style=map_style,
        tooltip={
            "html": "<b>{sample_id}</b><br/>Velocity: {velocity_label}<br/>Displacement: {displacement_label}",
            "style": {"backgroundColor": "#101b24", "color": "#e6f1f5", "fontSize": "12px"},
        },
    )
