import anchorpoint as ap
import apsync as aps
import os
import csv

def get_all_files(folder_path):
    print(f"Scanning folder: {folder_path}")
    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_list.append(os.path.join(root, file))
    print(f"Found {len(file_list)} files")
    return file_list

def get_all_attributes(api):
    print("Fetching all attributes from project/workspace...")
    return api.attributes.get_attributes()

def get_attribute_values(api, file_path, attributes):
    values = {}
    for attribute in attributes:
        try:
            value = api.attributes.get_attribute_value(file_path, attribute)
            if isinstance(value, aps.AttributeTagList):
                tag_names = [tag.name for tag in value]
                values[attribute.name] = ", ".join(tag_names)
            else:
                values[attribute.name] = value
        except Exception as e:
            print(f"Failed to get attribute '{attribute.name}' for '{file_path}': {e}")
            values[attribute.name] = ""
    return values

def export_to_csv(csv_path, data, header):
    print(f"Writing to CSV at {csv_path}")
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["File Path"] + header)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print("CSV export complete.")

def main():
    ctx = ap.get_context()
    ui = ap.UI()
    api = aps.get_api()

    selected_folder = ctx.path
    all_files = get_all_files(selected_folder)
    all_attributes = get_all_attributes(api)

    attribute_names = [attr.name for attr in all_attributes]
    export_data = []

    for file_path in all_files:
        attr_values = get_attribute_values(api, file_path, all_attributes)
        row = {"File Path": file_path}
        row.update(attr_values)
        export_data.append(row)

    export_path = os.path.join(selected_folder, "filelist.csv")
    export_to_csv(export_path, export_data, attribute_names)

    ui.show_success(f"Exported {len(all_files)} files to filelist.csv")

main()
