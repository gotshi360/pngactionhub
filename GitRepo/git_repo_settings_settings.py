import anchorpoint as ap
import apsync as aps

SETTINGS_NAME = "GitRepo"

ui = ap.UI()
ctx = ap.get_context()

local_settings  = aps.Settings(SETTINGS_NAME)
shared_settings = aps.SharedSettings(ctx.workspace_id, SETTINGS_NAME)


def save_connection(dialog: ap.Dialog):
    base_url = (dialog.get_value("base_url") or "").strip()
    token    = (dialog.get_value("token")    or "").strip()

    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        ui.show_error("Invalid Base URL", "Base URL must start with http:// or https://")
        return
    if not token:
        ui.show_error("Missing Token", "Please provide a Gitea Personal Access Token.")
        return

    ls = aps.Settings(SETTINGS_NAME)
    ls.set("base_url", base_url)
    ls.set("token",    token)
    ls.store()

    ui.show_success("Connection saved")


def save_visibility(dialog: ap.Dialog):
    ss = aps.SharedSettings(ctx.workspace_id, SETTINGS_NAME)
    ss.set("show_repo_settings", dialog.get_value("show_repo_settings"))
    ss.set("show_lfs_push",      dialog.get_value("show_lfs_push"))
    ss.set("rs_role_owner",   dialog.get_value("rs_role_owner"))
    ss.set("rs_role_admin",   dialog.get_value("rs_role_admin"))
    ss.set("rs_role_member",  dialog.get_value("rs_role_member"))
    ss.set("lfs_role_owner",  dialog.get_value("lfs_role_owner"))
    ss.set("lfs_role_admin",  dialog.get_value("lfs_role_admin"))
    ss.set("lfs_role_member", dialog.get_value("lfs_role_member"))
    ss.store()

    dialog.close()
    ui.show_success("Settings saved")


dialog = ap.Dialog()
dialog.title = "Git Repo Settings"

# ── Gitea connection ──────────────────────────────────────────────────────────
dialog.add_info("Gitea Connection")
dialog.add_text("Gitea Base URL").add_input(
    default=local_settings.get("base_url", ""),
    var="base_url",
    placeholder="https://gitea.example.com:3000",
    width=520,
)
dialog.add_text("Gitea Personal Access Token").add_input(
    default=local_settings.get("token", ""),
    var="token",
    placeholder="Paste token here",
    password=True,
    width=520,
)
dialog.add_button("Save Connection", callback=save_connection, primary=True)

dialog.add_empty()
dialog.add_separator()
dialog.add_empty()

# ── Git Repo Settings ─────────────────────────────────────────────────────────
dialog.start_section("Git Repo Settings", foldable=True, folded=False)
dialog.add_switch(
    shared_settings.get("show_repo_settings", True),
    var="show_repo_settings",
    text="Show action",
)
dialog.add_text("Visible to roles (workspace-wide):")
dialog.add_checkbox(shared_settings.get("rs_role_owner",  True), var="rs_role_owner",  text="Owner")
dialog.add_checkbox(shared_settings.get("rs_role_admin",  True), var="rs_role_admin",  text="Admin")
dialog.add_checkbox(shared_settings.get("rs_role_member", True), var="rs_role_member", text="Member")
dialog.end_section()

dialog.add_empty()

# ── Git LFS Push ──────────────────────────────────────────────────────────────
dialog.start_section("Git LFS Push", foldable=True, folded=False)
dialog.add_switch(
    shared_settings.get("show_lfs_push", True),
    var="show_lfs_push",
    text="Show action",
)
dialog.add_text("Visible to roles (workspace-wide):")
dialog.add_checkbox(shared_settings.get("lfs_role_owner",  True), var="lfs_role_owner",  text="Owner")
dialog.add_checkbox(shared_settings.get("lfs_role_admin",  True), var="lfs_role_admin",  text="Admin")
dialog.add_checkbox(shared_settings.get("lfs_role_member", True), var="lfs_role_member", text="Member")
dialog.end_section()

dialog.add_empty()
dialog.add_button("Save",   callback=save_visibility,       primary=True)
dialog.add_button("Cancel", callback=lambda d: d.close(),   primary=False)
dialog.show()
