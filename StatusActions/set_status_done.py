import anchorpoint
import apsync
import os
import pathlib


# ── Notification Hook ─────────────────────────────────────────────────────────

# ── Helper ────────────────────────────────────────────────────────────────────

def get_user_ids_from_attribute(path, attribute_name, ctx):
    api = anchorpoint.get_api()

    all_attrs  = api.attributes.get_attributes()
    candidates = [a for a in all_attrs if a.name == attribute_name]

    if not candidates:
        print(f"No attribute named '{attribute_name}' found in workspace.")
        return []

    raw_value = None
    for attr in candidates:
        val = api.attributes.get_attribute_value(path, attr)
        if val is not None:
            raw_value = val
            break

    if raw_value is None:
        return []

    raw_list = list(raw_value) if isinstance(raw_value, (list, tuple)) else [raw_value]
    raw_ids  = [v.id if hasattr(v, "id") else str(v) for v in raw_list]

    members         = apsync.get_project_members(ctx.workspace_id, ctx.project_id)
    member_by_id    = {m.id:    m.id for m in members}
    member_by_email = {m.email: m.id for m in members}

    matched = []
    for raw in raw_ids:
        if raw in member_by_id:
            matched.append(member_by_id[raw])
        elif raw in member_by_email:
            matched.append(member_by_email[raw])

    return matched


# ── Action ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ctx = anchorpoint.get_context()
    api = anchorpoint.get_api()
    ui  = anchorpoint.UI()

    path     = ctx.path
    filename = ctx.filename if ctx.filename else os.path.basename(path)

    if not ctx.project_id:
        ui.show_error("Not in a Project", "This action requires an active project context.")
    else:
        project      = api.get_project()
        project_name = project.name if project else "Unknown Project"
        username     = ctx.username

        relative_path = pathlib.Path(path).relative_to(ctx.project_path).as_posix()

        api.attributes.set_attribute_value(path, "Status", "Done")

        user_ids = get_user_ids_from_attribute(path, "Assigned", ctx)

        if not user_ids:
            ui.show_info("No Assignee", "Please select an assignee first.")
        else:
            message = (
                f"✅ <b>DONE</b> — "
                f"The status of '<font color='#dcc9f6'><b>{filename}</b></font>' from '<font color='#dcc9f6'><b>{project_name}</b></font>' "
                f"has changed to 'Done' by <font color='#dcc9f6'><b>{username}</b></font>."
            )
            anchorpoint.schedule_custom_notification(
                ctx.project_id,
                ctx.workspace_id,
                message,
                user_ids,
                {
                    "source":        "status_action",
                    "relative_path": relative_path,
                    "status":        "Done",
                },
            )
            ui.show_success("Status Updated", "Status set to 'Done'. Assignee(s) notified.")
