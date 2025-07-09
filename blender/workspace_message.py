import anchorpoint as ap

ctx = ap.get_context()
ui = ap.UI()

ui.show_info("workspace overview action clicked")

# Defines and shows the pages dialog
def show_dialog():
    dialog = ap.Dialog()
    dialog.title = "MAINTENANCE IN PROGRESS!"
    dialog.icon = ctx.icon
    dialog.add_text("Due to maintenance, GITEA is currently not functioning and files cannot be accessed")
    dialog.add_text("from within Anchorpoint. Please do not sync in Anchorpoint until the maintenance is over.")  
    dialog.add_info("You can still work on your files which you have on your local drive, just don't push it to the server. ")
    dialog.add_text(" ")
    dialog.add_text("Thank you for your patience.")
    dialog.add_info("Play'n GO Anchorpoint Support")
    dialog.show()


show_dialog()