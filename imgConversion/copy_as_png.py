# CHAT GPT PROMPT:
# Ez a script képekből készít PNG másolatokat, amiket vágólapra másol.
# Most módosítottuk, hogy a PNG-t a forrásfájl könyvtárába is elmentse, és több kijelölt fájlt is kezeljen.

import anchorpoint as ap
import apsync as aps
import os
import tempfile
import shutil

def create_temp_directory():
    return tempfile.mkdtemp()

def process_image(workspace_id, input_path, temp_dir):
    file_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # PNG generálása ideiglenes könyvtárba
    aps.generate_thumbnails(
        [input_path],
        temp_dir,
        with_detail=True,
        with_preview=False,
        workspace_id=workspace_id,
    )

    # PNG fájl elérési útja (_dt appendix-cel)
    generated_file = os.path.join(temp_dir, file_name + "_dt.png")

    if not os.path.exists(generated_file):
        print(f"HIBA: {generated_file} nem található.")
        return None

    # Átnevezés _dt nélkülire (vizuálisan szebb)
    renamed_file = os.path.join(temp_dir, file_name + ".png")
    os.rename(generated_file, renamed_file)

    print(f"PNG létrehozva: {renamed_file}")
    return renamed_file

def get_images(workspace_id, file_paths):
    progress = ap.Progress("PNG generálás", "Folyamatban...", infinite=False)
    ui = ap.UI()

    temp_dir = create_temp_directory()
    png_paths = []

    total = len(file_paths)
    for i, input_path in enumerate(file_paths):
        print(f"Feldolgozás: {input_path}")
        png_path = process_image(workspace_id, input_path, temp_dir)

        if png_path:
            # PNG másolása az eredeti könyvtárba
            destination_path = os.path.join(os.path.dirname(input_path), os.path.basename(png_path))
            shutil.copyfile(png_path, destination_path)
            print(f"Másolva ide: {destination_path}")
            png_paths.append(png_path)

        progress.report_progress((i + 1) / total)

    # Vágólapra másolás, ha legalább egy PNG sikerült
    if png_paths:
        ap.copy_files_to_clipboard(png_paths)
        ui.show_success("PNG másolatok létrehozva", f"{len(png_paths)} fájl másolva a vágólapra és mappába.")
    else:
        ui.show_error("Hiba", "Egyik fájlból sem sikerült PNG-t generálni.")

    progress.finish()

ctx = ap.get_context()
ctx.run_async(get_images, ctx.workspace_id, ctx.selected_files)
