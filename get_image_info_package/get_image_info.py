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
                mode_to_bits = {
                    "1": 1, "L": 8, "P": 8, "RGB": 24, "RGBA": 32,
                    "CMYK": 32, "I": 32, "F": 32
                }
                bit_depth = mode_to_bits.get(img.mode, "Unknown")
        return f"{width} x {height}", f"{int(resolution)} dpi", f"{bit_depth}-bit"
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, None, None

def set_attributes(ctx, file_path, dimensions, resolution, bit_depth, settings):
    api = aps.get_api()
    api.set_workspace(ctx.workspace_id)

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
        api.attributes.set_attribute_value(file_path, name, value)

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
        set_attributes(ctx, file, dimensions, resolution, bit_depth, {
            "show_dimensions": show_dimensions,
            "show_resolution": show_resolution,
            "show_bit_depth": show_bit_depth
        })

    ui.show_success("Metadata extraction completed.")

main()
