import anchorpoint as ap
import sys
import os
import subprocess

ctx = ap.get_context()
ui = ap.UI()

is_windows = sys.platform == "win32"
is_mac = sys.platform == "darwin"

if is_windows:
    AP_BASE = os.path.join(os.environ.get("APPDATA", ""), "Anchorpoint Software", "Anchorpoint")
    SCRIPTS_DIR = os.path.join(AP_BASE, "app", "scripts", "win")
elif is_mac:
    AP_BASE = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Anchorpoint Software", "Anchorpoint")
    SCRIPTS_DIR = None
else:
    AP_BASE = ""
    SCRIPTS_DIR = None

LOG_DIR = os.path.join(AP_BASE, "logs") if AP_BASE else ""
LOG_FILE = os.path.join(LOG_DIR, "ap.log") if LOG_DIR else ""


def _run_bat(bat_name, dialog):
    bat_path = os.path.join(SCRIPTS_DIR, bat_name)
    if not os.path.exists(bat_path):
        ui.show_error("Script Not Found", f"Could not find the script:\n{bat_path}")
        return
    dialog.close()
    try:
        subprocess.Popen(bat_path, shell=True)
        print(f"[Troubleshooting] Running: {bat_name}")
    except Exception as e:
        ui.show_error("Error", f"Failed to run {bat_name}:\n{str(e)}")
        ap.log_error(f"[Troubleshooting] Failed to run {bat_name}: {e}")


def on_clear_settings(dialog):
    _run_bat("clear_settings.bat", dialog)


def on_clear_settings_and_database(dialog):
    _run_bat("clear_settings_and_database.bat", dialog)


def on_clear_window_settings(dialog):
    _run_bat("clear_window_settings.bat", dialog)


def on_copy_log(dialog):
    if not LOG_FILE or not os.path.exists(LOG_FILE):
        ui.show_error("Log Not Found", f"Log file not found:\n{LOG_FILE}")
        return
    try:
        ap.copy_files_to_clipboard([LOG_FILE])
        ui.show_success("Copied", "Log file has been copied to clipboard.")
        print(f"[Troubleshooting] Log file copied to clipboard: {LOG_FILE}")
    except Exception as e:
        ui.show_error("Error", f"Failed to copy log file:\n{str(e)}")
        ap.log_error(f"[Troubleshooting] Failed to copy log file: {e}")


def on_open_log_folder(dialog):
    if not LOG_DIR or not os.path.exists(LOG_DIR):
        ui.show_error("Folder Not Found", f"Log folder not found:\n{LOG_DIR}")
        return
    try:
        if is_windows:
            subprocess.Popen(["explorer", LOG_DIR])
        elif is_mac:
            subprocess.Popen(["open", LOG_DIR])
        else:
            subprocess.Popen(["xdg-open", LOG_DIR])
        print(f"[Troubleshooting] Opened log folder: {LOG_DIR}")
    except Exception as e:
        ui.show_error("Error", f"Failed to open log folder:\n{str(e)}")
        ap.log_error(f"[Troubleshooting] Failed to open log folder: {e}")


def show_dialog():
    dialog = ap.Dialog()
    dialog.title = "Troubleshooting"
    dialog.icon = ctx.icon

    # --- Debug Actions section ---
    dialog.start_section("Debug Actions", foldable=False)

    if not is_windows:
        dialog.add_info("<i>The scripts below are Windows-only and are unavailable on this platform.</i>")

    dialog.add_text("🗑️ <b>Clear Settings</b>").add_button(
        "Run", callback=on_clear_settings, primary=False, enabled=is_windows
    )
    dialog.add_info("Resets all Anchorpoint application settings to their defaults.")

    dialog.add_text("🗄️ <b>Clear Settings and Database</b>").add_button(
        "Run", callback=on_clear_settings_and_database, primary=False, enabled=is_windows
    )
    dialog.add_info("Resets settings and clears the local database. Use when Anchorpoint behaves unexpectedly.")

    dialog.add_text("🪟 <b>Clear Window Settings</b>").add_button(
        "Run", callback=on_clear_window_settings, primary=False, enabled=is_windows
    )
    dialog.add_info("Resets saved window positions and layout to their defaults.")

    dialog.end_section()

    # --- Logs section ---
    dialog.start_section("Logs", foldable=False)

    dialog.add_text("📋 <b>Copy Log File to Clipboard</b>").add_button(
        "Copy", callback=on_copy_log, primary=False
    )
    dialog.add_info("Copies the latest Anchorpoint log file (ap.log) to your clipboard as a file.")

    dialog.add_text("📂 <b>Open Log Folder</b>").add_button(
        "Open", callback=on_open_log_folder, primary=False
    )
    dialog.add_info("Opens the folder containing Anchorpoint log files in your system file manager.")

    dialog.end_section()

    dialog.show()


show_dialog()
