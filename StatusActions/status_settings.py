import anchorpoint
import apsync

SETTINGS_NAME = "StatusActions"

VISIBLE_OPTIONS = ["Everyone", "Owner & Admins only", "Owner only"]


if __name__ == "__main__":
    settings = apsync.Settings(SETTINGS_NAME)

    show_done       = settings.get("show_done",       True)
    show_inprogress = settings.get("show_inprogress", True)
    show_review     = settings.get("show_review",     True)
    visible_to      = settings.get("visible_to",      "Everyone")

    def save(dialog):
        s = apsync.Settings(SETTINGS_NAME)
        s.set("show_done",       dialog.get_value("show_done"))
        s.set("show_inprogress", dialog.get_value("show_inprogress"))
        s.set("show_review",     dialog.get_value("show_review"))
        s.set("visible_to",      dialog.get_value("visible_to"))
        s.store()
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
    dialog.add_text("Actions visible to:")
    dialog.add_dropdown(visible_to, VISIBLE_OPTIONS, var="visible_to")

    dialog.add_empty()
    dialog.add_button("Save",   callback=save,                primary=True)
    dialog.add_button("Cancel", callback=lambda d: d.close(), primary=False)

    dialog.show()
