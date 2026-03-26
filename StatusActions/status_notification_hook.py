import anchorpoint
import pathlib
import os

# Keep references alive so the OS notification callback is not garbage-collected
# before the user clicks it.
_pending = []


def on_custom_notification(message, meta_data, project_id, project_path, ctx):
    print(f"[StatusAction] on_custom_notification fired — project_path={project_path!r}, meta_data={meta_data!r}")

    if not meta_data:
        return
    if meta_data.get("source") != "status_action":
        return

    relative_path = meta_data.get("relative_path")
    if not relative_path:
        print("[StatusAction] No relative_path in metadata.")
        return

    if not project_path:
        print("[StatusAction] project_path is empty — cannot reconstruct path.")
        return

    full_path = str(pathlib.Path(project_path) / relative_path)
    print(f"[StatusAction] Reconstructed path: {full_path!r}")

    notification_message = meta_data.get("message", message)

    ui = anchorpoint.UI()

    def navigate():
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
        # Remove from pending after navigation
        _pending[:] = [(u, n) for (u, n) in _pending if n is not navigate]

    # Store both ui and navigate to prevent garbage collection
    _pending.append((ui, navigate))
    print(f"[StatusAction] Pending notifications: {len(_pending)}")

    ui.show_system_notification(
        "Anchorpoint",
        notification_message,
        callback=navigate,
    )
