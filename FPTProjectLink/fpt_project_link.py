import anchorpoint
import apsync
import webbrowser

SETTINGS_ID = "fpt::project_link::v1"


def _get_settings(ctx):
    return apsync.SharedSettings(ctx.project_id, ctx.workspace_id, SETTINGS_ID)


def on_is_action_enabled(path, type, ctx):
    """Hide sidebar button when no link is configured or visibility is disabled."""
    if not ctx.project_id or not ctx.workspace_id:
        return False
    try:
        settings = _get_settings(ctx)
        url = settings.get("link_url", "")
        show = settings.get("show_in_sidebar", False)
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
