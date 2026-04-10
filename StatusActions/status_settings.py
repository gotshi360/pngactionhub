import anchorpoint
import apsync

SETTINGS_NAME = "StatusActions"

VISIBLE_OPTIONS = ["Everyone", "Owner & Admins only", "Owner only"]


if __name__ == "__main__":
    ctx = anchorpoint.get_context()

    # Per-user local settings (personal visibility preferences)
    local_settings  = apsync.Settings(SETTINGS_NAME)
    show_done       = local_settings.get("show_done",       True)
    show_inprogress = local_settings.get("show_inprogress", True)
    show_review     = local_settings.get("show_review",     True)

    # Workspace-wide shared setting (role restriction applies to everyone)
    shared_settings = apsync.SharedSettings(ctx.workspace_id, SETTINGS_NAME)
    visible_to      = shared_settings.get("visible_to", "Everyone")

    def save(dialog):
        ls = apsync.Settings(SETTINGS_NAME)
        ls.set("show_done",       dialog.get_value("show_done"))
        ls.set("show_inprogress", dialog.get_value("show_inprogress"))
        ls.set("show_review",     dialog.get_value("show_review"))
        ls.store()

        ss = apsync.SharedSettings(ctx.workspace_id, SETTINGS_NAME)
        ss.set("visible_to", dialog.get_value("visible_to"))
        ss.store()

        anchorpoint.UI().show_success("Settings Saved", "Status Actions settings updated.")
        dialog.close()

    dialog = anchorpoint.Dialog()
    dialog.title = "Status Actions: Settings"
    dialog.icon = ":/icons/settings.svg"

    dialog.add_text("Show in context menu:")
    dialog.add_switch(show_done,       var="show_done",       text="Set Status: Done")
    dialog.add_switch(show_inprogress, var="show_inprogress", text="Set Status: In Progress")
    dialog.add_switch(show_review,     var="show_review",     text="Set Status: Review")

    dialog.add_empty()
    dialog.add_text("Actions visible to (workspace-wide):")
    dialog.add_dropdown(visible_to, VISIBLE_OPTIONS, var="visible_to")

    dialog.add_empty()
    dialog.add_button("Save",   callback=save,                primary=True)
    dialog.add_button("Cancel", callback=lambda d: d.close(), primary=False)

    dialog.show()
