# CHAT GPT PROMPT:
# Export all attributes of selected files or folders into a CSV file.
# Handle all types including single and multiple choice tags.

import anchorpoint as ap
import apsync as aps
import csv
import os

ctx = ap.get_context()
ui = ap.UI()
api = aps.get_api()

def get_attribute_value_str(value):
    if value is None:
        return ""
    # Handle multiple choice tags
    if isinstance(value, apsync.AttributeTagList):
        return ", ".join(tag.name for tag in value)
    # Handle single choice tags
    if isinstance(value, apsync.AttributeTag):
        return value.name
    # Handle regular list
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)

def export_attributes_to_csv(selected_items):
    print("Starting to export attributes...")

    attributes = api.attributes.get_attributes()
    if not attributes:
        ui.show_info("No attributes found in project.")
        return

    print(f"Found {len(attributes)} attributes")

    csv_path = os.path.join(ctx.yaml_dir, "exported_attributes.csv")

    with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Path", "Attribute Name", "Attribute Type", "Value"])

        for item in selected_items:
            for attribute in attributes:
                try:
                    value = api.attributes.get_attribute_value(item, attribute)
                    value_str = get_attribute_value_str(value)
                    writer.writerow([item, attribute.name, attribute.type, value_str])
                except Exception as e:
                    print(f"Error reading attribute '{attribute.name}' on {item}: {e}")

    ui.show_success(f"Exported to {csv_path}")
    print("Export completed.")

def main():
    if ctx.type == ap.Type.File:
        selected_items = ctx.selected_files
    elif ctx.type == ap.Type.Folder:
        selected_items = ctx.selected_folders
    else:
        ui.show_error("Unsupported context")
        return

    if not selected_items:
        ui.show_info("No files or folders selected")
        return

    export_attributes_to_csv(selected_items)

main()