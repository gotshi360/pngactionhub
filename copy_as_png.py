import anchorpoint as ap
import apsync as aps
import os
import tempfile

import subprocess, sys

def run_hidden(cmd):
    startupinfo = None
    if sys.platform.startswith("win"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)


def convert_with_imagemagick(input_path, temp_dir):
    action_root = os.path.dirname(__file__)
    magick_path = os.path.join(action_root, "tools", "imagemagick", "magick.exe")

    if not os.path.exists(magick_path):
        print(f"ERROR: magick.exe not found at {magick_path}")
        return None

    output_path = os.path.join(temp_dir, os.path.splitext(os.path.basename(input_path))[0] + ".png")

    result = run_hidden([magick_path, f"{input_path}[0]", output_path])
    if result.returncode != 0:
        print("ImageMagick error:", result.stderr)
        return None

    return output_path

def copy_images_to_clipboard(workspace_id, file_paths):
    progress = ap.Progress("Generating PNGs", infinite=False)
    progress.set_cancelable(True)

    ui = ap.UI()
    temp_dir = tempfile.mkdtemp()
    png_paths = []

    total = len(file_paths)
    for i, input_path in enumerate(file_paths):
        if progress.canceled:
            progress.finish()
            ui.show_info("Process Canceled", "PNG generation was interrupted by the user.")
            return

        filename = os.path.basename(input_path)
        progress.set_text(f"Processing {filename}")
        print(f"Processing: {input_path}")

        png_path = convert_with_imagemagick(input_path, temp_dir)
        if png_path:
            png_paths.append(png_path)

        progress.report_progress((i + 1) / total)

    progress.finish()

    if png_paths:
        ap.copy_files_to_clipboard(png_paths)
        ui.show_success("PNG Copied", f"{len(png_paths)} PNG(s) copied to clipboard.")
    else:
        ui.show_error("Error", "Failed to generate PNG(s).")

ctx = ap.get_context()
ctx.run_async(copy_images_to_clipboard, ctx.workspace_id, ctx.selected_files)
