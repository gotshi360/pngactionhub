import anchorpoint
import pathlib
import os


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

    def navigate():
        print(f"[StatusAction] Navigating to: {full_path!r}")
        ui = anchorpoint.UI()
        if os.path.isfile(full_path):
            ui.navigate_to_file(full_path)
        elif os.path.isdir(full_path):
            ui.navigate_to_folder(full_path)
        else:
            print(f"[StatusAction] Path does not exist on this machine: {full_path!r}")

    anchorpoint.UI().show_system_notification(
        "Anchorpoint",
        message,
        callback=navigate,
    )
