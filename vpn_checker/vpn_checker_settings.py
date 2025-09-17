import anchorpoint as ap
import apsync

ctx = ap.get_context()
ui = ap.UI()

settings = apsync.Settings("vpn_checker")

def store(dialog):
    try:
        interval = int(dialog.get_value("interval"))
        vpn_url = dialog.get_value("vpn_url").strip()

        settings.set("interval", interval)
        settings.set("vpn_url", vpn_url)
        settings.store()

        ui.show_success("Settings saved")
        dialog.close()
    except ValueError:
        ui.show_error("Interval must be an integer")

def show_settings():
    interval = str(settings.get("interval", 15))
    vpn_url = settings.get("vpn_url", "https://gitea.playngo.com")

    dialog = ap.Dialog()
    dialog.title = "VPN Checker Settings"
    dialog.icon = ctx.icon

    dialog.add_text("Check Interval (seconds)	").add_input(interval, var="interval")
    dialog.add_text("Test URL	").add_input(vpn_url, var="vpn_url")
    dialog.add_info("VPN is considered active if this URL is reachable.")

    dialog.add_button("Save", callback=store)

    dialog.show()

show_settings()
