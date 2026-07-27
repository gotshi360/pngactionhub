import anchorpoint
import apsync
import time
import webbrowser

SETTINGS_ID = "fpt::project_link::v1"

# on_is_action_enabled decides whether the sidebar button is drawn, so it runs
# far more often than a context menu hook. SharedSettings is cloud backed, so
# the two values it needs are cached per project for a short window.
_SIDEBAR_CACHE_TTL = 30.0
_sidebar_cache = {}  # (project_id, workspace_id) -> (timestamp, url, show)


def _get_settings(ctx):
    return apsync.SharedSettings(ctx.project_id, ctx.workspace_id, SETTINGS_ID)


def _get_sidebar_config(ctx):
    key = (ctx.project_id, ctx.workspace_id)
    now = time.monotonic()
    cached = _sidebar_cache.get(key)
    if cached and (now - cached[0]) < _SIDEBAR_CACHE_TTL:
        return cached[1], cached[2]

    settings = _get_settings(ctx)
    url = settings.get("link_url", "")
    show = settings.get("show_in_sidebar", False)
    _sidebar_cache[key] = (now, url, show)
    return url, show


def on_is_action_enabled(path, type, ctx):
    """Hide sidebar button when no link is configured or visibility is disabled."""
    if not ctx.project_id or not ctx.workspace_id:
        return False
    try:
        url, show = _get_sidebar_config(ctx)
        return bool(show) and bool(url.strip())
    except Exception as e:
        print(f"FPT Project Link [on_is_action_enabled]: {e}")
        return False


if __name__ == "__main__":
    ctx = anchorpoint.get_context()
    ui = anchorpoint.UI()

    if not ctx.project_id:
        ui.show_error("No Project", "FPT Project Link requires an active project.")
        exit()

    try:
        settings = _get_settings(ctx)
        url = settings.get("link_url", "").strip()
    except Exception as e:
        print(f"FPT Project Link [open]: {e}")
        ui.show_error("FPT Project Link", "Could not read project settings.")
        exit()

    if not url:
        ui.show_info("FPT Project Link", "No link has been configured for this project yet.")
        exit()

    webbrowser.open(url)
