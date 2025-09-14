# CHAT GPT PROMPT:
# This script converts selected image files to PNG format and saves them next to the original files.
# It now includes a cancelable progress bar and shows the current file being processed.

import anchorpoint as ap
import apsync as aps
import os
import tempfile
import shutil

def create_temp_directory():
    return tempfile.mkdtemp()

def process_image_and_save(workspace_id, input_path, temp_dir):
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
        print(f"ERROR: PNG not found for {input_path}")
        return None

    renamed_file = os.path.join(temp_dir, file_name + ".png")
    os.rename(generated_file, renamed_file)

    destination_path = os.path.join(os.path.dirname(input_path), os.path.basename(renamed_file))
    shutil.copyfile(renamed_file, destination_path)
    print(f"Saved PNG to: {destination_path}")
    return destination_path

def save_pngs(workspace_id, file_paths):
    progress = ap.Progress("Saving PNGs", infinite=False)
    progress.set_cancelable(True)

    ui = ap.UI()
    temp_dir = create_temp_directory()
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

        saved_path = process_image_and_save(workspace_id, input_path, temp_dir)
        if saved_path:
            saved_paths.append(saved_path)

        progress.report_progress((i + 1) / total)

    progress.finish()

    if saved_paths:
        ui.show_success("PNG Saved", f"{len(saved_paths)} PNG(s) saved next to source file(s).")
    else:
        ui.show_error("Error", "No PNGs were saved.")

ctx = ap.get_context()
ctx.run_async(save_pngs, ctx.workspace_id, ctx.selected_files)
