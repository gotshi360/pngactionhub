import anchorpoint as ap
from PIL import Image
import os

def convert_images_to_png():
    ctx = ap.get_context()
    ui = ap.UI()
    selected_files = ctx.selected_files
    total = len(selected_files)

    progress = ap.Progress("Saving as PNG", infinite=False)
    progress.set_cancelable(True)

    for idx, file in enumerate(selected_files):
        if progress.canceled:
            print("Operation cancelled by user.")
            break

        base, ext = os.path.splitext(file)
        output_path = base + ".png"

        progress.set_text(f"Converting: {os.path.basename(file)}")
        print(f"Processing {file}")

        try:
            image = Image.open(file)
            image.save(output_path, "PNG")
        except Exception as e:
            print(f"Failed to convert {file}: {e}")

        progress.report_progress((idx + 1) / total)

    progress.finish()
    ui.show_success("PNG export finished.")

def main():
    ctx = ap.get_context()
    ctx.run_async(convert_images_to_png)

main()
