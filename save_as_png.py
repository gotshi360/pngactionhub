import anchorpoint as ap
import apsync as aps
import os

import subprocess, sys

def run_hidden(cmd):
    startupinfo = None
    if sys.platform.startswith("win"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)


def convert_with_imagemagick(input_path, output_path):
    action_root = os.path.dirname(__file__)
    magick_path = os.path.join(action_root, "tools", "imagemagick", "magick.exe")

    if not os.path.exists(magick_path):
        print(f"ERROR: magick.exe not found at {magick_path}")
        return False

    result = run_hidden([magick_path, f"{input_path}[0]", output_path])
    if result.returncode != 0:
        print("ImageMagick error:", result.stderr)
        return False

    return True

def save_pngs(workspace_id, file_paths):
    progress = ap.Progress("Saving PNGs", infinite=False)
    progress.set_cancelable(True)

    ui = ap.UI()
    saved_paths = []

    total = len(file_paths)
    for i, input_path in enumerate(file_paths):
        if progress.canceled:
            progress.finish()
            ui.show_info("Process Canceled", "PNG saving was interrupted by the user.")
            return

        filename = os.path.basename(input_path)
        progress.set_text(f"Processing {filename}")
        print(f"Processing: {input_path}")

        destination_path = os.path.splitext(input_path)[0] + ".png"
        if convert_with_imagemagick(input_path, destination_path):
            saved_paths.append(destination_path)
            print(f"Saved PNG to: {destination_path}")

        progress.report_progress((i + 1) / total)

    progress.finish()

    if saved_paths:
        ui.show_success("PNG Saved", f"{len(saved_paths)} PNG(s) saved next to source file(s).")
    else:
        ui.show_error("Error", "No PNGs were saved.")

ctx = ap.get_context()
ctx.run_async(save_pngs, ctx.workspace_id, ctx.selected_files)
