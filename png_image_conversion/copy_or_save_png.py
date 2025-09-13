import anchorpoint as ap
import apsync as aps
import os
import tempfile
import shutil


def create_temp_directory():
    return tempfile.mkdtemp()


def generate_png(input_path, workspace_id, output_dir):
    aps.generate_thumbnails(
        [input_path],
        output_dir,
        with_detail=True,
        with_preview=False,
        workspace_id=workspace_id,
    )
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    generated_path = os.path.join(output_dir, f"{base_name}_dt.png")
    final_path = os.path.join(output_dir, f"{base_name}.png")

    if not os.path.exists(generated_path):
        return None

    os.rename(generated_path, final_path)
    return final_path


def copy_to_clipboard(selected_files, workspace_id):
    progress = ap.Progress("Copying images to clipboard", infinite=False)
    temp_dir = create_temp_directory()
    image_paths = []

    for index, file in enumerate(selected_files):
        progress.set_text(f"Processing {os.path.basename(file)}")
        png_path = generate_png(file, workspace_id, temp_dir)
        if png_path:
            image_paths.append(png_path)
        progress.report_progress((index + 1) / len(selected_files))

    if image_paths:
        ap.copy_files_to_clipboard(image_paths)
        ap.UI().show_success("Images copied to clipboard")
    else:
        ap.UI().show_error("No images copied", "Thumbnail generation failed")

    progress.finish()


def save_png_next_to_source(selected_files, workspace_id):
    progress = ap.Progress("Saving PNGs next to source files", infinite=False)
    temp_dir = create_temp_directory()
    saved_count = 0

    for index, file in enumerate(selected_files):
        progress.set_text(f"Generating for {os.path.basename(file)}")
        png_temp_path = generate_png(file, workspace_id, temp_dir)
        if png_temp_path:
            target_path = os.path.join(os.path.dirname(file), os.path.basename(png_temp_path))
            shutil.copy(png_temp_path, target_path)
            saved_count += 1
        progress.report_progress((index + 1) / len(selected_files))

    if saved_count:
        ap.UI().show_success(f"{saved_count} PNG file(s) saved")
    else:
        ap.UI().show_error("No files saved", "Thumbnail generation failed")

    progress.finish()


def show_action_dialog(ctx):
    dialog = ap.Dialog()
    dialog.title = "Choose PNG Action"
    dialog.icon = ctx.icon

    dialog.add_button("📋 Copy to Clipboard", callback=lambda d: ctx.run_async(copy_to_clipboard, ctx.selected_files, ctx.workspace_id), primary=True)
    dialog.add_button("💾 Save PNG Next to File", callback=lambda d: ctx.run_async(save_png_next_to_source, ctx.selected_files, ctx.workspace_id), primary=False)

    dialog.show()


def main():
    ctx = ap.get_context()

    if not ctx.selected_files:
        ap.UI().show_info("No files selected", "Please select one or more supported files")
        return

    show_action_dialog(ctx)


main()
