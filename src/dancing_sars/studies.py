"""Study-area settings for the synthetic surface-change demo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StudyArea:
    id: str
    name: str
    region: str
    phenomenon: str
    description: str
    longitude: float
    latitude: float
    zoom: float
    velocity_base_m_year: float
    velocity_peak_m_year: float
    ripple_m_year: float
    heading_deg: float
    heading_variation_deg: float
    display_scale: float
    grid_lon_step: float
    grid_lat_step: float
    id_prefix: str

    def public_dict(self) -> dict[str, str | float]:
        return {
            "id": self.id,
            "name": self.name,
            "region": self.region,
            "phenomenon": self.phenomenon,
            "description": self.description,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "zoom": self.zoom,
        }


STUDY_AREAS: tuple[StudyArea, ...] = (
    StudyArea(
        id="jakobshavn",
        name="Jakobshavn Glacier",
        region="Greenland · Arctic",
        phenomenon="Glacier flow",
        description="A synthetic ice-flow scene on Greenland’s west coast.",
        longitude=-49.70,
        latitude=69.20,
        zoom=7.1,
        velocity_base_m_year=142,
        velocity_peak_m_year=355,
        ripple_m_year=19,
        heading_deg=226,
        heading_variation_deg=11,
        display_scale=3.4,
        grid_lon_step=0.031,
        grid_lat_step=0.022,
        id_prefix="JAK",
    ),
    StudyArea(
        id="thwaites",
        name="Thwaites Glacier",
        region="West Antarctica · Southern Ocean",
        phenomenon="Glacier flow",
        description="A second synthetic ice-flow scene in the Amundsen Sea sector.",
        longitude=-106.70,
        latitude=-75.20,
        zoom=6.8,
        velocity_base_m_year=220,
        velocity_peak_m_year=580,
        ripple_m_year=25,
        heading_deg=205,
        heading_variation_deg=14,
        display_scale=4.0,
        grid_lon_step=0.12,
        grid_lat_step=0.045,
        id_prefix="THW",
    ),
    StudyArea(
        id="kilauea",
        name="Kīlauea Volcano",
        region="Hawaiʻi Island · Pacific",
        phenomenon="Volcanic deformation",
        description="A low-rate synthetic ground-motion field around the volcano.",
        longitude=-155.285,
        latitude=19.421,
        zoom=9.2,
        velocity_base_m_year=0.004,
        velocity_peak_m_year=0.018,
        ripple_m_year=0.0018,
        heading_deg=48,
        heading_variation_deg=38,
        display_scale=8_000,
        grid_lon_step=0.018,
        grid_lat_step=0.012,
        id_prefix="KIL",
    ),
    StudyArea(
        id="san-andreas",
        name="San Andreas Fault",
        region="California · North America",
        phenomenon="Tectonic deformation",
        description="A synthetic slow-motion field along a major plate boundary.",
        longitude=-120.85,
        latitude=36.35,
        zoom=7.8,
        velocity_base_m_year=0.003,
        velocity_peak_m_year=0.014,
        ripple_m_year=0.0012,
        heading_deg=315,
        heading_variation_deg=26,
        display_scale=12_000,
        grid_lon_step=0.035,
        grid_lat_step=0.018,
        id_prefix="SAF",
    ),
)

STUDY_BY_ID = {study.id: study for study in STUDY_AREAS}
