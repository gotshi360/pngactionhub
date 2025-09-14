import anchorpoint as ap
import apsync as aps
from PIL import Image
import os

def convert_to_png_with_progress():
    ctx = ap.get_context()
    ui = ap.UI()
    settings = aps.Settings()

    selected_files = ctx.selected_files
    total = len(selected_files)
    save_to_subfolder = settings.get("save_to_subfolder", False)

    progress = ap.Progress("Saving as PNG", infinite=False)
    progress.set_cancelable(True)

    for index, file in enumerate(selected_files):
        if progress.canceled:
            print("Operation cancelled by user")
            break

        base, ext = os.path.splitext(file)
        folder = os.path.dirname(file)

        # Determine output path
        if save_to_subfolder:
            subfolder = os.path.join(folder, "_png")
            os.makedirs(subfolder, exist_ok=True)
            output_path = os.path.join(subfolder, os.path.basename(base) + ".png")
        else:
            output_path = base + ".png"

        progress.set_text(f"Converting: {os.path.basename(file)}")
        print(f"Saving to: {output_path}")

        try:
            image = Image.open(file)
            image.save(output_path, "PNG")
        except Exception as e:
            print(f"Failed to convert {file}: {e}")

        progress.report_progress((index + 1) / total)

    progress.finish()
    ui.show_success("PNG export finished.")

def main():
    ctx = ap.get_context()
    ctx.run_async(convert_to_png_with_progress)

main()
