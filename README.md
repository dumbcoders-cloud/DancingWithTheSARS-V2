# Dancing with the SARs

A Python surface-change visualizer prototype for a NASA Space Apps Challenge. The interface explores synthetic observations around four study areas: Jakobshavn and Thwaites glaciers, Kīlauea volcano, and the San Andreas Fault. **The displacement observations are simulated, not NISAR measurements. The map can display real, date-matched MODIS Terra true-color imagery from NASA GIBS as visual context; this optical imagery is not the source of the simulated displacement values.**

## Run locally

Requires Python 3.10–3.14 and internet access for NASA GIBS imagery, the remote fallback basemap, and web fonts.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8501`. On macOS or Linux, activate with `source .venv/bin/activate` and use the same pip and Python commands.

The page has study selection, light/dark themes, a time slider and playback, playback speed, map layer switches (including date-matched NASA imagery), a history chart, metrics, hover details, and CSV export. The theme choice is saved in browser local storage.

## NASA data used

The map requests date-specific **MODIS Terra Corrected Reflectance True Color** imagery from NASA's Global Imagery Browse Services (GIBS). The NASA layer follows the selected observation date and can be toggled on/off. It provides real satellite imagery for geographic context; it is optical imagery, not SAR displacement data. All motion vectors, displacement values, and timeline metrics remain explicitly simulated.

- Resource name for the NASA Data form: **NASA Global Imagery Browse Services (GIBS) — MODIS Terra Corrected Reflectance True Color**
- GIBS WMTS service: <https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/>
- API documentation: <https://nasa-gibs.github.io/gibs-api-docs/access-basics/>

## Architecture

- **FastAPI + Uvicorn** provide the local JSON API and serve the application process.
- **Flask + Jinja** provide the HTML shell and static CSS/JavaScript. FastAPI mounts Flask through `a2wsgi`.
- **PyDeck / Deck.gl** render the interactive map and simulated movement layers.
- **PyWebView** embeds the locally served page in a resizable native desktop window.
- **PyInstaller** builds the Windows one-file, windowed executable with the generated icon.

See [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for component details, API routes, limitations, full setup steps, and troubleshooting. The judge-facing presenter script is in [HACKATHON_TALK_TRACK.txt](HACKATHON_TALK_TRACK.txt).

## Windows desktop executable

Install the desktop/build dependencies and launch the source window:

```powershell
python -m pip install -r requirements-desktop.txt
python scripts/launch_desktop.py
```

Build a Windows `.exe` from Windows PowerShell:

```powershell
.\scripts\build_windows.ps1
```

The result is `dist/DancingWithTheSARs.exe`. The script creates `assets/dancing_with_the_sars.ico` and its PNG preview before building. The target computer needs the Microsoft Edge WebView2 Runtime. PyInstaller output is not code-signed; deployment environments can require signing or allow-listing.

## API quick reference

- `GET /api/health`
- `GET /api/studies`
- `GET /api/studies/{study_id}/history`
- `GET /api/studies/{study_id}/observations/{index}`
- `GET /api/studies/{study_id}/observations/{index}/map` (query options include `theme`, `vectors`, `footprint`, and `nasa_imagery`)
- `GET /api/studies/{study_id}/observations/{index}/csv`
- Interactive API docs: `http://127.0.0.1:8501/api/docs`

## Platform scope

This repository currently configures and builds a Windows desktop `.exe`. Linux WebView backend packaging and Android APK packaging are future work; there is no functional APK build command yet. The source web interface can be run locally in a browser on other platforms where Python dependencies are available.
