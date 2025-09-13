# CHAT GPT PROMPT: 
# Ez az action kinyeri a kiválasztott kép fájlok (PNG, JPG, PSD, PSB) metadatait: Dimensions, Resolution, Bit Depth.
# A Settings dialog checkboxai alapján állítja be az Anchorpoint attribútumokat.

import anchorpoint as ap
import apsync as aps
from PIL import Image
from psd_tools import PSDImage

def extract_image_info(file_path):
    print(f"Extracting info from: {file_path}")
    suffix = file_path.lower().split('.')[-1]

    try:
        if suffix in ["psd", "psb"]:
            psd = PSDImage.open(file_path)
            width, height = psd.width, psd.height
            resolution = int(psd.image_resources.get_data("resolution_info").dpi) if psd.image_resources.has("resolution_info") else 72
            bit_depth = psd.header.depth
        else:
            with Image.open(file_path) as img:
                width, height = img.size
                resolution = img.info.get("dpi", (72, 72))[0]
                bit_depth = len(img.getbands()) * img.bits
        return f"{width} x {height}", f"{int(resolution)} dpi", f"{bit_depth}-bit"
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, None, None

def set_attributes(ctx, dimensions, resolution, bit_depth, settings):
    api = aps.get_api()
    api.set_workspace(ctx.workspace_id)
    project = api.get_project()
    if not project:
        print("No project found")
        return

    attributes_to_set = []

    if settings.get("show_dimensions", True):
        attributes_to_set.append(("Dimensions", dimensions))
    if settings.get("show_resolution", True):
        attributes_to_set.append(("Resolution", resolution))
    if settings.get("show_bit_depth", True):
        attributes_to_set.append(("Bit Depth", bit_depth))

    for name, value in attributes_to_set:
        print(f"Setting attribute {name}: {value}")
        if value is None:
            continue
        api.attributes.set_attribute_value(ctx.path, name, value)

def main():
    ctx = ap.get_context()
    ui = ap.UI()

    print("Starting metadata extraction...")

    settings = aps.Settings()
    show_dimensions = settings.get("show_dimensions", True)
    show_resolution = settings.get("show_resolution", True)
    show_bit_depth = settings.get("show_bit_depth", True)

    for file in ctx.selected_files:
        dimensions, resolution, bit_depth = extract_image_info(file)
        set_attributes(ctx, dimensions, resolution, bit_depth, {
            "show_dimensions": show_dimensions,
            "show_resolution": show_resolution,
            "show_bit_depth": show_bit_depth
        })

    ui.show_success("Metadata extraction completed.")

main()
