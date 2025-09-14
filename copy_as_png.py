# CHAT GPT PROMPT:
# This script converts selected image files to PNG format and copies them to the clipboard.
# It now includes a cancelable progress bar and shows the current file being processed.

import anchorpoint as ap
import apsync as aps
import os
import tempfile

def create_temp_directory():
    return tempfile.mkdtemp()

def process_image(workspace_id, input_path, temp_dir):
    file_name = os.path.splitext(os.path.basename(input_path))[0]

    # Generate PNG thumbnail in the temp directory
    aps.generate_thumbnails(
        [input_path],
        temp_dir,
        with_detail=True,
        with_preview=False,
        workspace_id=workspace_id,
    )

    generated_file = os.path.join(temp_dir, file_name + "_dt.png")
    if not os.path.exists(generated_file):
        print(f"ERROR: Generated PNG not found: {generated_file}")
        return None

    renamed_file = os.path.join(temp_dir, file_name + ".png")
    os.rename(generated_file, renamed_file)
    return renamed_file

def copy_images_to_clipboard(workspace_id, file_paths):
    progress = ap.Progress("Generating PNGs", infinite=False)
    progress.set_cancelable(True)

    ui = ap.UI()
    temp_dir = create_temp_directory()
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

        png_path = process_image(workspace_id, input_path, temp_dir)
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
