import content_database
import patches # Needed to apply monkey patching
import pathlib
import patoolib
import re
import shutil
import sys
import threading
import time

from helper.config_operations import get_library_path, get_debug_mode
from helper.file_operations import create_temp_folder, delete_temp_folder
from patoolib.util import PatoolError


temp_folder = 'temp/'


lock = threading.Lock()

if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = pathlib.Path(__file__).parents
seven_zip_path = pathlib.Path(str(base_path)).joinpath( "7z\\7z.exe")


# Define the target folders
target_folders = [
    "aniBlocks", "data", "Environments", "Light Presets", "People",
    "Props", "ReadMe's", "Render Presets", "Render Settings", "Runtime",
    "Scenes", "Scripts", "Shader Presets", "Cameras", "Documentation"
]


def get_relative_path(full_path):
    # Join all target folders into a regex pattern, escaping special characters if any
    pattern = r'|'.join([re.escape(folder) for folder in target_folders])

    # Search for the first occurrence of any target folder in the path
    match = re.search(pattern, full_path)

    # If a match is found, extract the path from the target folder onward
    if match:
        start_index = match.start()  # Get the starting index of the match
        return full_path[start_index:]  # Return substring from target folder onward
    else:
        return full_path  # Return original path if no target folder is found

def clean_temp_folder():
    shutil.rmtree(temp_folder)
    pathlib.Path(temp_folder).mkdir(parents=True, exist_ok=True)

# Extract archives in the download folder and move content to temp folder
def extract_archive(item_path, is_debug_mode):
        base_item_name = pathlib.Path(item_path).name
        if base_item_name.lower().endswith(('.zip', '.rar', '7z', '.tar')):
            print(f"Extracting: {base_item_name}")
            try:
                verbosity = 2 if is_debug_mode else -1
                patoolib.extract_archive(item_path, outdir=temp_folder, verbosity=verbosity, interactive=False, program=str(seven_zip_path))
                time.sleep(1)
                return True
            except PatoolError as e:
                print(f"The archive {base_item_name} can not be extracted: {e}")
                return False

# Removes everything in temp folder that is not one of the target folders before importing to library
def clean_folder(folder_path):
    for item_path in pathlib.Path(folder_path).iterdir():
        item = item_path.name
        if item_path.is_dir() and item not in target_folders:
            shutil.rmtree(item_path)
        elif item_path.is_file():
            item_path.unlink()

def add_to_database(root_path, item):
    archive_name = item.stem.split(".")[0]
    file_list = []

    # Traverse through all files in the directory
    for item in pathlib.Path(root_path).iterdir():
        for root, dirs, files in pathlib.Path(item).walk():
            if files:
                for file in files:
                    file_list.append(str((pathlib.Path(get_relative_path(str(root))).joinpath(file))))
    if content_database.archive_exist(archive_name, file_list):
        return True
    print(f"Archive '{archive_name}' added to the database with {len(file_list)} files.")
    content_database.add_archive(archive_name, file_list)
    time.sleep(1)


# Searching the content of extracted archive for target folders
def traverse_directory(folder_path, current_item, is_debug_mode):
    archive_extracted = False
    for root, dirs, files in pathlib.Path(folder_path).walk():
        for file in files:
            if file.lower().endswith(('.zip', '.rar', '7z', '.tar')):
                verbosity = 2 if is_debug_mode else -1
                patoolib.extract_archive(str(pathlib.Path(str(root)).joinpath(file)), outdir=str(root), verbosity=verbosity,
                                             interactive=False, program=str(seven_zip_path))
                time.sleep(0.5)
                pathlib.Path(root).joinpath(file).unlink()
                archive_extracted = True
        if archive_extracted:
            return traverse_directory(folder_path, current_item, is_debug_mode)
        if any(target in dirs for target in target_folders):
            clean_folder(root)
            if add_to_database(root, current_item):
                return False
            shutil.copytree(root, get_library_path(), dirs_exist_ok=True)
            return True
    return False

def start_installer_gui(file_path, is_delete_archive=False):

    with lock:
        create_temp_folder()
        clean_temp_folder()
        if not extract_archive(file_path, get_debug_mode()):
            clean_temp_folder()
            return
        if traverse_directory(temp_folder, pathlib.Path(file_path), get_debug_mode()):
            print(f"{file_path} was successfully imported to your library")
        else:
            print(f"{file_path} can not be automatically imported because it doesn't have the right folder structure")
            print(f"or the archive already exists in the database")
        clean_temp_folder()
        delete_temp_folder()
        if is_delete_archive:
            pathlib.Path(file_path).unlink()