import anchorpoint as ap

ctx = ap.get_context()
ui = ap.UI()
path = ctx.path


def create_file(dialog):
    file_name = dialog.get_value("file_name")
    content = dialog.get_value("content")
    with open(os.path.join(path, file_name), "w") as f:
        f.write(content)

    dialog.close()
    ap.UI().show_success(f"File {file_name} created")


# Defines and shows the pages dialog
def show_dialog():
    dialog = ap.Dialog()
    dialog.title = "MAINTENANCE IN PROGRESS!"
    dialog.icon = ctx.icon
    dialog.add_text("Due to maintenance, GITEA is currently not functioning and files cannot be accessed")
    dialog.add_text("from within Anchorpoint. Please do not sync in Anchorpoint until the maintenance is over.")  
    dialog.add_text("You can still work on your files which you have on your local drive, just don't push it to the server. ")
    dialog.add_text(" ")
    dialog.add_text("Thank you for your patience.")
    dialog.add_info("Play'n GO Anchorpoint Support")
    dialog.show()


show_dialog()

