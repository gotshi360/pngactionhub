import anchorpoint
import apsync
import re
import webbrowser

try:
    import requests
except ImportError:
    _ctx = anchorpoint.get_context()
    _ctx.install("requests")
    import requests

SETTINGS_NAME    = "ProjectLinks"
DEFAULT_GDD_BASE = "https://gdds.playngo.com"


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_asset_number(description: str):
    match = re.search(r'asset[-_](\d+)', description, re.IGNORECASE)
    return int(match.group(1)) if match else None


def find_gdd_url(asset_number: int, base_url: str):
    """
    Fetches {base_url}/index.json and finds the entry whose name contains
    GameID{asset_number} (leading zeros ignored).

    Returns (url: str | None, error: str | None)
    """
    index_url  = f"{base_url}/index.json"
    game_id_re = re.compile(r'GameID0*(\d+)', re.IGNORECASE)

    try:
        resp = requests.get(index_url, timeout=15)
    except requests.RequestException as exc:
        return None, (
            f"Could not reach the GDD server.\n\n"
            f"URL: {index_url}\n\n"
            f"Check your network connection or verify the server URL in the ProjectLinks settings.\n"
            f"Details: {exc}"
        )

    if not resp.ok:
        return None, (
            f"The GDD server returned an error (HTTP {resp.status_code}).\n\n"
            f"The server may be temporarily unavailable. Please try again later.\n"
            f"URL: {index_url}"
        )

    try:
        data = resp.json()
    except ValueError:
        return None, (
            "The GDD index file could not be read — the server returned an unexpected response.\n\n"
            "Contact your administrator if this issue persists."
        )

    if not isinstance(data, dict):
        return None, (
            "The GDD index file has an unexpected format and cannot be parsed.\n\n"
            "Contact your administrator if this issue persists."
        )

    for path_key in data:
        m = game_id_re.search(path_key)
        if m and int(m.group(1)) == asset_number:
            url = path_key if path_key.startswith("http") else f"{base_url}/{path_key.lstrip('/')}"
            return url, None

    return None, (
        f"No GDD entry found for GameID {asset_number}.\n\n"
        f"Make sure the asset number in the project description matches an existing game in the GDD index.\n"
        f"If the game was recently added, the GDD index may not have been updated yet."
    )


# ── Action entry point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctx = anchorpoint.get_context()
    api = anchorpoint.get_api()
    ui  = anchorpoint.UI()

    # ── 1. Load project description ───────────────────────────────────────────
    project = api.get_project()
    if not project:
        ui.show_error("No Project", "Please open a project first.")
        raise SystemExit

    description  = project.description or ""
    asset_number = extract_asset_number(description)

    if asset_number is None:
        ui.show_error(
            "Asset ID Not Found",
            "No asset number was found in the project description.\n\n"
            "Add the game's asset ID in the format  asset-1048  to the project description and try again.",
        )
        raise SystemExit

    # ── 2. Read settings ──────────────────────────────────────────────────────
    ss       = apsync.SharedSettings(ctx.workspace_id, SETTINGS_NAME)
    base_url = ss.get("gdd_base_url", DEFAULT_GDD_BASE).rstrip("/")

    # ── 3. Find GDD URL ───────────────────────────────────────────────────────
    progress = anchorpoint.Progress("GDD", f"Looking up GameID {asset_number}…")
    url, error = find_gdd_url(asset_number, base_url)
    progress.finish()

    # ── 4. Open or report ─────────────────────────────────────────────────────
    if url:
        webbrowser.open(url)
        ui.show_success("GDD", f"Opened GDD for asset-{asset_number}")
    else:
        ui.show_error("GDD – Not Found", error or "No URL found.")
