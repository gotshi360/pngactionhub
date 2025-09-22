import anchorpoint as ap
import apsync as aps
from PIL import Image
from pymediainfo import MediaInfo
from psd_tools import PSDImage
import os
import tempfile
import shutil
import subprocess
import sys

def run_hidden(cmd):
    startupinfo = None
    if sys.platform.startswith("win"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)

def extract_resolution_via_temp_png(file_path):
    try:
        temp_dir = tempfile.mkdtemp()
        temp_png = os.path.join(temp_dir, "temp_resolution.png")

        action_root = os.path.dirname(__file__)
        magick_path = os.path.join(action_root, "tools", "imagemagick", "magick.exe")

        if not os.path.exists(magick_path):
            print(f"magick.exe not found at: {magick_path}")
            return "Unknown"

        result = run_hidden([magick_path, f"{file_path}[0]", temp_png])
        if result.returncode != 0 or not os.path.exists(temp_png):
            print("ImageMagick conversion failed:", result.stderr)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return "Unknown"

        with Image.open(temp_png) as img:
            dpi = img.info.get("dpi")
            dpi_val = round(dpi[0]) if dpi else 72

        os.remove(temp_png)
        shutil.rmtree(temp_dir, ignore_errors=True)

        return f"{dpi_val} DPI"

    except Exception as e:
        print(f"Error extracting resolution via temp PNG: {e}")
        return "Unknown"

def extract_image_info(file_path, workspace_id, settings):
    suffix = file_path.lower().split('.')[-1]

    try:
        if suffix in ["psb", "psd"]:
            psd = PSDImage.open(file_path)
            width, height = psd.size
            layer_count = len(list(psd.descendants()))

            result = {
                "Dimensions": f"{width} x {height}",
                "Layer Count": str(layer_count),
            }

            if settings.get("show_resolution", True):
                result["Resolution"] = extract_resolution_via_temp_png(file_path)

            return result

        else:
            with Image.open(file_path) as img:
                width, height = img.size
                result = {"Dimensions": f"{width} x {height}"}

                if settings.get("show_resolution", True):
                    dpi = img.info.get("dpi")
                    if dpi:
                        dpi_val = round(dpi[0])
                        result["Resolution"] = f"{dpi_val} DPI"

            return result

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
            "Resolution": "show_resolution",
            "Frame Rate": "show_frame_rate",
            "Bitrate": "show_bitrate",
            "Duration": "show_duration",
            "Layer Count": "show_layer_count"
        }

        key = key_map.get(name)
        if not key or not settings.get(key, True):
            continue

        print(f"Setting {name} = {value}")
        api.attributes.set_attribute_value(file_path, name, value)

def run_with_progress():
    ctx = ap.get_context()
    ui = ap.UI()
    settings = aps.Settings()

    supported_suffixes = [".png", ".jpg", ".jpeg", ".psd", ".psb", ".mp4", ".mov"]
    selected_files = list(ctx.selected_files)

    recursive = settings.get("recursive", False)
    for folder in ctx.selected_folders:
        if recursive:
            for root, dirs, files in os.walk(folder):
                for entry in files:
                    path = os.path.join(root, entry)
                    if os.path.splitext(path)[1].lower() in supported_suffixes:
                        selected_files.append(path)
        else:
            for entry in os.listdir(folder):
                path = os.path.join(folder, entry)
                if os.path.isfile(path) and os.path.splitext(path)[1].lower() in supported_suffixes:
                    selected_files.append(path)

    total = len(selected_files)
    progress = ap.Progress("Extracting Metadata", infinite=False)
    progress.set_cancelable(True)

    for idx, file in enumerate(selected_files):
        if progress.canceled:
            print("Operation canceled by user.")
            break

        suffix = os.path.splitext(file)[1].lower()
        progress.set_text(f"Processing: {os.path.basename(file)}")
        print(f"Processing {file}")

        if suffix in [".png", ".jpg", ".jpeg", ".psd", ".psb"]:
            attributes = extract_image_info(file, ctx.workspace_id, settings)
        elif suffix in [".mp4", ".mov"]:
            attributes = extract_video_info(file)
        else:
            print(f"Unsupported file type: {suffix}")
            progress.report_progress((idx + 1) / total)
            continue

        set_attributes(file, attributes, ctx, settings)
        progress.report_progress((idx + 1) / total)

    progress.finish()
    ui.show_success("Metadata extraction completed.")

def main():
    ctx = ap.get_context()
    ctx.run_async(run_with_progress)

main()
