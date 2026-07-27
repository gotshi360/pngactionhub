import anchorpoint
import apsync
import time

SETTINGS_ID = "fpt::project_link::v1"

# on_is_action_enabled runs on every folder context menu open, so the access
# lookup is cached per workspace instead of being repeated on each right click.
_ACCESS_CACHE_TTL = 30.0
_access_cache = {}  # workspace_id -> (timestamp, access_str)


def _get_settings(ctx):
    return apsync.SharedSettings(ctx.project_id, ctx.workspace_id, SETTINGS_ID)


def _get_access_str(workspace_id):
    now = time.monotonic()
    cached = _access_cache.get(workspace_id)
    if cached and (now - cached[0]) < _ACCESS_CACHE_TTL:
        return cached[1]

    access_str = str(apsync.get_workspace_access(workspace_id)).lower()
    _access_cache[workspace_id] = (now, access_str)
    print(f"FPT Project Link [settings]: workspace access = {access_str}")
    return access_str


def _is_admin_or_owner(ctx):
    """Return True if the current user is a workspace owner or admin."""
    access_str = _get_access_str(ctx.workspace_id)
    return "owner" in access_str or "admin" in access_str


def on_is_action_enabled(path, type, ctx):
    """Show the settings menu entry only for project owners and admins."""
    if not ctx.project_id or not ctx.workspace_id:
        return False
    return _is_admin_or_owner(ctx)


def _save(dialog):
    ctx = anchorpoint.get_context()
    url = dialog.get_value("url").strip()
    show = dialog.get_value("show_in_sidebar")

    try:
        settings = _get_settings(ctx)
        settings.set("link_url", url)
        settings.set("show_in_sidebar", show)
        settings.store()
        anchorpoint.UI().show_success("FPT Project Link", "Settings saved successfully.")
    except Exception as e:
        print(f"FPT Project Link [settings save]: {e}")
        anchorpoint.UI().show_error("FPT Project Link", "Failed to save settings.")

    dialog.close()


if __name__ == "__main__":
    ctx = anchorpoint.get_context()
    ui = anchorpoint.UI()

    if not ctx.project_id:
        ui.show_error("No Project", "FPT Project Link Settings requires an active project.")
        exit()

    if not _is_admin_or_owner(ctx):
        ui.show_error(
            "Access Denied",
            "Only project owners and admins can configure FPT Project Link."
        )
        exit()

    try:
        settings = _get_settings(ctx)
        current_url = settings.get("link_url", "")
        current_show = settings.get("show_in_sidebar", True)
    except Exception as e:
        print(f"FPT Project Link [settings load]: {e}")
        current_url = ""
        current_show = True

    dialog = anchorpoint.Dialog()
    dialog.title = "FPT Project Link — Settings"

    dialog.add_text("<b>Project Link URL</b>")
    dialog.add_input(
        default=current_url,
        placeholder="https://",
        var="url",
        width=320
    )
    dialog.add_info(
        "The URL will open in the browser when any project member clicks "
        "the <b>FPT Project Link</b> button in the sidebar. "
        "Each project can have its own link."
    )

    dialog.add_empty()
    dialog.add_separator()
    dialog.add_empty()

    dialog.add_text("<b>Sidebar Visibility</b>")
    dialog.add_switch(
        default=current_show,
        var="show_in_sidebar",
        text="Show FPT Project Link in the sidebar for this project"
    )

    dialog.add_empty()
    dialog.add_button("Save", callback=_save)
    dialog.add_button("Cancel", callback=lambda d: d.close(), primary=False)

    dialog.show()
