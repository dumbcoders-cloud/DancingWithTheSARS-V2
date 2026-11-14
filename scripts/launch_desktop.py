"""Run the local FastAPI and Flask application inside a native pywebview window."""

from __future__ import annotations

import multiprocessing
import os
import socket
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
from pathlib import Path

APP_TITLE = "Dancing with the SARs — Surface Change Visualizer"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]


def log_file_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    log_dir = base / "DancingWithTheSARs" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


def available_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run_local_server(port: int) -> None:
    """Start Uvicorn in a child process so pywebview can own the GUI thread."""
    log_stream = log_file_path().open("a", encoding="utf-8", buffering=1)
    sys.stdout = log_stream
    sys.stderr = log_stream

    root = app_root()
    sys.path.insert(0, str(root / "src"))
    import uvicorn

    from dancing_sars.server import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )


def wait_for_server(server: multiprocessing.Process, port: int, timeout: float = 45.0) -> str:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    app_url = f"http://127.0.0.1:{port}"
    while time.monotonic() < deadline:
        if not server.is_alive():
            raise RuntimeError("The local API server stopped during startup.")
        try:
            with urlopen(f"{app_url}/api/health", timeout=1.5) as response:
                if response.status == 200 and b'"status":"ok"' in response.read():
                    return app_url
        except (OSError, URLError) as error:
            last_error = error
        time.sleep(0.25)
    raise TimeoutError(f"The local dashboard did not become ready: {last_error or 'startup timed out'}")


def show_error(message: str) -> None:
    """Show startup failures in the windowed build where no console is visible."""
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, APP_TITLE, 0x10)
    else:
        print(message, file=sys.stderr)


def stop_server(server: multiprocessing.Process) -> None:
    if server.pid is None:
        return
    if not server.is_alive():
        server.join(timeout=0.2)
        return
    server.terminate()
    server.join(timeout=5)
    if server.is_alive():
        server.kill()
        server.join(timeout=2)


def main() -> None:
    # PyInstaller's --windowed mode leaves standard streams unset.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

    port = available_local_port()
    server = multiprocessing.Process(
        target=run_local_server,
        args=(port,),
        name="DancingWithTheSARs-Server",
    )
    try:
        server.start()
        app_url = wait_for_server(server, port)
        import webview

        # The dashboard's CSV download button should open a native Save dialog.
        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.create_window(
            APP_TITLE,
            app_url,
            width=1440,
            height=960,
            min_size=(960, 680),
            background_color="#081116",
            text_select=True,
        )
        renderer = "edgechromium" if sys.platform == "win32" else None
        webview.start(gui=renderer, debug=False, private_mode=True)
    except Exception as error:
        try:
            log_path = log_file_path()
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"Desktop startup error: {error!r}\n")
        except OSError:
            log_path = Path("app.log")
        show_error(
            "Dancing with the SARs could not start its desktop window.\n\n"
            f"Details: {error}\n\n"
            "On Windows, make sure the Microsoft Edge WebView2 Runtime is installed. "
            f"Diagnostic log: {log_path}"
        )
    finally:
        stop_server(server)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
