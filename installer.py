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
from helper.file_operations import create_temp_folder, delete_temp_folder, create_logger
from patoolib.util import PatoolError

logger = create_logger()

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
            logger.info(f"Extracting {base_item_name}")
            try:
                verbosity = 2 if is_debug_mode else -1
                patoolib.extract_archive(item_path, outdir=temp_folder, verbosity=verbosity, interactive=False, program=str(seven_zip_path))
                time.sleep(1)
                return True
            except PatoolError as e:
                logger.error(f"The archive {base_item_name} can not be extracted: {e}")
                return False

# Removes everything in temp folder that is not one of the target folders before importing to library
def clean_folder(folder_path):
    for item_path in pathlib.Path(folder_path).iterdir():
        if item_path.is_file():
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
    if content_database.does_archive_exist(archive_name, file_list):
        logger.info(f"Archive '{archive_name}' already exists in the database.")
        return True
    logger.info(f"Adding archive '{archive_name}' with {len(file_list)} files to the database.")
    content_database.add_archive(archive_name, file_list)
    time.sleep(1)


# Searching the content of extracted archive for target folders
def traverse_directory(folder_path, current_item, progressbar, is_debug_mode, is_nested_archive = False):
    archive_extracted = False
    manifest_exists = False
    for root, dirs, files in pathlib.Path(folder_path).walk():
        for file in files:
            if file.lower().endswith(('.zip', '.rar', '7z', '.tar')):
                logger.info(f"Extracting nested archive: {file}")
                verbosity = 2 if is_debug_mode else -1
                patoolib.extract_archive(str(pathlib.Path(str(root)).joinpath(file)), outdir=str(root), verbosity=verbosity,
                                             interactive=False, program=str(seven_zip_path))
                time.sleep(0.5)
                pathlib.Path(root).joinpath(file).unlink()
                archive_extracted = True
            if file.lower().endswith("manifest.dsx"):
                manifest_exists = True

        progressbar.set(progressbar.get() + 0.1)
        if archive_extracted:
            progressbar.set(progressbar.get()+0.1)
            is_nested_archive = archive_extracted
            return traverse_directory(folder_path, current_item, progressbar,  is_debug_mode, is_nested_archive)
        if manifest_exists:
            for folder in dirs:
                if folder.lower().startswith("content"):
                    content_path = pathlib.Path(str(root)).joinpath(folder)
                    progressbar.set(0.9)
                    clean_folder(content_path)
                    if add_to_database(content_path, current_item):
                        return False
                    shutil.copytree(content_path, get_library_path(), dirs_exist_ok=True)
                    return True
        if any(target in dirs for target in target_folders):
            progressbar.set(0.9)
            clean_folder(root)
            if add_to_database(root, current_item):
                return False
            shutil.copytree(root, get_library_path(), dirs_exist_ok=True)
            return True
    return False

def start_installer_gui(file_path, progressbar, is_delete_archive=False) -> bool:
    is_archive_imported = False
    with lock:
        logger.info(f"Installing {file_path}")
        create_temp_folder()
        clean_temp_folder()
        progressbar.set(0.1)
        if not extract_archive(file_path, get_debug_mode()):
            clean_temp_folder()
            return is_archive_imported
        progressbar.set(0.4)
        if traverse_directory(temp_folder, pathlib.Path(file_path), progressbar,  get_debug_mode()):
            is_archive_imported = True
            logger.info(f"Successfully imported: {file_path}")

        else:
            is_archive_imported = False
            logger.warning(f"Failed to import {file_path}. Invalid folder structure or asset already exists.")
        clean_temp_folder()
        delete_temp_folder()
        if is_delete_archive:
            pathlib.Path(file_path).unlink()
            logger.info(f"Deleted archive: {file_path}")
        return is_archive_imported