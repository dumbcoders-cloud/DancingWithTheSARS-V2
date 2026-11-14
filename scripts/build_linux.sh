#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "$script_dir/.." && pwd)"
cd "$project_dir"

python3 -m pip install -r requirements-desktop.txt
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --windowed \
  --name DancingWithTheSARs \
  --collect-all fastapi \
  --collect-all flask \
  --collect-all a2wsgi \
  --collect-all uvicorn \
  --collect-all pydeck \
  --collect-all webview \
  --add-data "src:src" \
  --add-data "assets:assets" \
  scripts/launch_desktop.py

if ! command -v appimagetool >/dev/null 2>&1; then
  echo "PyInstaller created dist/DancingWithTheSARs. Install appimagetool to wrap it as an AppImage." >&2
  exit 1
fi

app_dir="$project_dir/dist/DancingWithTheSARs.AppDir"
expected_app_dir="$project_dir/dist/DancingWithTheSARs.AppDir"
if [[ "$app_dir" != "$expected_app_dir" || "$app_dir" != "$project_dir"/dist/* ]]; then
  echo "Refusing to remove an AppDir outside the project dist folder." >&2
  exit 1
fi
rm -rf -- "$app_dir"
mkdir -p "$app_dir/usr/bin"
cp dist/DancingWithTheSARs "$app_dir/usr/bin/DancingWithTheSARs"
cp assets/mission-mark.svg "$app_dir/dancing-with-the-sars.svg"
cat > "$app_dir/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/DancingWithTheSARs" "$@"
EOF
chmod +x "$app_dir/AppRun"
cat > "$app_dir/dancing-with-the-sars.desktop" <<'EOF'
[Desktop Entry]
Name=Dancing with the SARs
Exec=DancingWithTheSARs
Icon=dancing-with-the-sars
Type=Application
Categories=Science;Education;
Terminal=false
EOF
appimagetool "$app_dir" "dist/DancingWithTheSARs.AppImage"
echo "Linux AppImage: dist/DancingWithTheSARs.AppImage"
