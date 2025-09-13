import anchorpoint as ap
import apsync as aps
from PIL import Image
from pymediainfo import MediaInfo
import os

def extract_image_info(file_path):
    suffix = file_path.lower().split('.')[-1]

    try:
        if suffix == "psb":
            from psd_tools import PSDImage
            psb = PSDImage.open(file_path)
            width, height = psb.size
            return {
                "Dimensions": f"{width} x {height}"
            }
        else:
            with Image.open(file_path) as img:
                width, height = img.size
            return {
                "Dimensions": f"{width} x {height}"
            }
    except Exception as e:
        print(f"Error reading image {file_path}: {e}")
        return {}

def extract_video_info(file_path):
    try:
        media_info = MediaInfo.parse(file_path)
        for track in media_info.tracks:
            if track.track_type == "Video":
                width = track.width or 0
                height = track.height or 0
                dimensions = f"{width} x {height}" if width and height else "Unknown"
                frame_rate = f"{float(track.frame_rate):.2f} fps" if track.frame_rate else "Unknown"
                bitrate = f"{int(track.bit_rate) // 1000} kbps" if track.bit_rate else "Unknown"
                duration_sec = (track.duration or 0) / 1000
                minutes = int(duration_sec // 60)
                seconds = int(duration_sec % 60)
                duration = f"{minutes:02}:{seconds:02}" if duration_sec else "Unknown"
                return {
                    "Dimensions": dimensions,
                    "Frame Rate": frame_rate,
                    "Bitrate": bitrate,
                    "Duration": duration
                }
        return {}
    except Exception as e:
        print(f"Error reading video {file_path}: {e}")
        return {}

def set_attributes(file_path, attributes, ctx, settings):
    api = aps.get_api()
    api.set_workspace(ctx.workspace_id)

    for name, value in attributes.items():
        key_map = {
            "Dimensions": "show_video_dimensions" if file_path.lower().endswith(('.mp4', '.mov')) else "show_dimensions",
            "Frame Rate": "show_frame_rate",
            "Bitrate": "show_bitrate",
            "Duration": "show_duration"
        }

        key = key_map.get(name)
        if not key or not settings.get(key, True):
            continue

        print(f"Setting {name} = {value}")
        api.attributes.set_attribute_value(file_path, name, value)

def main():
    ctx = ap.get_context()
    ui = ap.UI()
    settings = aps.Settings()

    print("Starting metadata extraction...")

    for file in ctx.selected_files:
        suffix = os.path.splitext(file)[1].lower()

        if suffix in [".png", ".jpg", ".jpeg", ".psd", ".psb"]:
            attributes = extract_image_info(file)
        elif suffix in [".mp4", ".mov"]:
            attributes = extract_video_info(file)
        else:
            print(f"Unsupported file type: {suffix}")
            continue

        set_attributes(file, attributes, ctx, settings)

    ui.show_success("Metadata extraction completed.")

main()
