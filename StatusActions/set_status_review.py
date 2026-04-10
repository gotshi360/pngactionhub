import anchorpoint
import apsync
import os
import pathlib


# ── Visibility Hook ───────────────────────────────────────────────────────────

def on_is_action_enabled(path, type, ctx):
    settings = apsync.Settings("StatusActions")
    if not settings.get("show_review", True):
        return False
    return _is_role_allowed(settings, ctx)


def _is_role_allowed(settings, ctx):
    visible_to = settings.get("visible_to", "Everyone")
    if visible_to == "Everyone":
        return True
    access = apsync.get_workspace_access(ctx.workspace_id)
    if visible_to == "Owner only":
        return access == apsync.AccessLevel.Owner
    if visible_to == "Owner & Admins only":
        return access in (apsync.AccessLevel.Owner, apsync.AccessLevel.Admin)
    return True


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

        api.attributes.set_attribute_value(path, "Status", "Pending Review")

        user_ids = get_user_ids_from_attribute(path, "Reviewer", ctx)

        if not user_ids:
            ui.show_info("No Reviewer", "Please select a reviewer first.")
        else:
            message = (
                f"🔍 APPROVAL PENDING — "
                f"A Review has been requested for '{filename}' from '{project_name}' "
                f"by {username}."
            )
            anchorpoint.schedule_custom_notification(
                ctx.project_id,
                ctx.workspace_id,
                message,
                user_ids,
                {
                    "source":        "status_action",
                    "relative_path": relative_path,
                    "status":        "Pending Review",
                },
            )
            ui.show_success("Status Updated", "Status set to 'Pending Review'. Reviewer(s) notified.")
