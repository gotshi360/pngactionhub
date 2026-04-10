import anchorpoint
import pathlib
import os

# Keep references alive so the OS notification callback is not garbage-collected
# before the user clicks it.
_pending = []


def _resolve_path(meta_data, project_path):
    """Reconstruct the full path from relative_path + project_path in metadata."""
    if not meta_data:
        return None

    relative_path = meta_data.get("relative_path")
    if not relative_path:
        print("[StatusAction] No relative_path in metadata.")
        return None

    if not project_path:
        print("[StatusAction] project_path is empty — cannot reconstruct path.")
        return None

    full_path = str(pathlib.Path(project_path) / relative_path)
    print(f"[StatusAction] Reconstructed path: {full_path!r}")
    return full_path


def _navigate_to_path(full_path):
    """Open the given file or folder in Anchorpoint."""
    print(f"[StatusAction] navigate() called for: {full_path!r}")
    print(f"[StatusAction] isfile={os.path.isfile(full_path)}, isdir={os.path.isdir(full_path)}")
    nav_ui = anchorpoint.UI()
    if os.path.isfile(full_path):
        print(f"[StatusAction] Calling navigate_to_file")
        nav_ui.navigate_to_file(full_path)
    elif os.path.isdir(full_path):
        print(f"[StatusAction] Calling navigate_to_folder")
        nav_ui.navigate_to_folder(full_path)
    else:
        print(f"[StatusAction] Path does not exist on this machine: {full_path!r}")


def _is_status_notification(meta_data):
    """Return True if this notification was sent by a Set Status action."""
    return bool(meta_data and meta_data.get("source") == "status_action")


# ── Hook: notification received ───────────────────────────────────────────────

def on_custom_notification(message, meta_data, project_id, project_path, ctx):
    print(f"[StatusAction] on_custom_notification fired — project_path={project_path!r}, meta_data={meta_data!r}")

    if not _is_status_notification(meta_data):
        return

    full_path = _resolve_path(meta_data, project_path)
    if not full_path:
        return

    ui = anchorpoint.UI()

    def navigate():
        _navigate_to_path(full_path)
        # Remove from pending after navigation
        _pending[:] = [(u, n) for (u, n) in _pending if n is not navigate]

    # Store both ui and navigate to prevent garbage collection
    _pending.append((ui, navigate))
    print(f"[StatusAction] Pending notifications: {len(_pending)}")

    ui.show_system_notification(
        "Anchorpoint",
        message,
        callback=navigate,
    )


# ── Hook: notification clicked (in-app) ───────────────────────────────────────

def on_custom_notification_navigation(message, meta_data, project_id, project_path, ctx):
    """
    Triggered when the user clicks a notification inside Anchorpoint.
    Overrides the default navigation (project folder) and jumps directly
    to the specific file or folder that was status-updated.
    """
    print(f"[StatusAction] on_custom_notification_navigation fired — project_path={project_path!r}, meta_data={meta_data!r}")

    if not _is_status_notification(meta_data):
        return

    full_path = _resolve_path(meta_data, project_path)
    if not full_path:
        return

    _navigate_to_path(full_path)
