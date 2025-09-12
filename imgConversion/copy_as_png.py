# CHAT GPT PROMPT:
# This script converts selected image files to PNG format, copies them to the clipboard,
# and also saves them into the original folder of the source files.

import anchorpoint as ap
import apsync as aps
import os
import tempfile
import shutil

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

    # Thumbnail will have "_dt" suffix
    generated_file = os.path.join(temp_dir, file_name + "_dt.png")

    if not os.path.exists(generated_file):
        print(f"ERROR: Generated PNG not found: {generated_file}")
        return None

    # Rename to clean filename
    renamed_file = os.path.join(temp_dir, file_name + ".png")
    os.rename(generated_file, renamed_file)

    print(f"PNG created: {renamed_file}")
    return renamed_file

def get_images(workspace_id, file_paths):
    progress = ap.Progress("Generating PNGs", "Please wait...", infinite=False)
    ui = ap.UI()

    temp_dir = create_temp_directory()
    png_paths = []

    total = len(file_paths)
    for i, input_path in enumerate(file_paths):
        print(f"Processing: {input_path}")
        png_path = process_image(workspace_id, input_path, temp_dir)

        if png_path:
            # Copy PNG to the original folder
            destination_path = os.path.join(os.path.dirname(input_path), os.path.basename(png_path))
            shutil.copyfile(png_path, destination_path)
            print(f"Copied to: {destination_path}")
            png_paths.append(png_path)

        progress.report_progress((i + 1) / total)

    # Copy to clipboard
    if png_paths:
        ap.copy_files_to_clipboard(png_paths)
        ui.show_success("PNG Copies Created", f"{len(png_paths)} file(s) copied to clipboard and saved.")
    else:
        ui.show_error("Error", "Could not generate a PNG from any of the selected files.")

    progress.finish()

ctx = ap.get_context()
ctx.run_async(get_images, ctx.workspace_id, ctx.selected_files)
