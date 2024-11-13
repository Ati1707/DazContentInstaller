import pathlib
import sys
import time
import shutil
import configparser
import re
import threading

import patoolib
from patoolib.util import PatoolError

import content_database
import patches # Needed to apply monkey patching
from helper.file_operations import create_temp_folder, delete_temp_folder


# Class to create colored output
class Bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

download_folder = 'downloads/'
temp_folder = 'temp/'

config = configparser.ConfigParser()
config.read("config.ini")
library_path = config["PATH"]["LibraryPath"]
is_debug_mode = config["DEBUG"].getboolean("IsDebugMode")


lock = threading.Lock()

if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = pathlib.Path(__file__).parents
seven_zip_path = pathlib.Path(str(base_path)).joinpath( "7z\\7z.exe")

if not library_path or library_path == "example":
    print(f"{Bcolors.WARNING}You need to set a asset library path in the config.ini{Bcolors.ENDC}")
    print(f"{Bcolors.WARNING}Create a new folder don't use an existing folder{Bcolors.ENDC}")
    print(f"{Bcolors.WARNING}This tool is not stable yet!!! Data loss can occur if you use an existing folder{Bcolors.ENDC}")
    sys.exit(0)

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
                if is_debug_mode:
                    patoolib.extract_archive(item_path, outdir=temp_folder, verbosity= 2, interactive=False, program=str(seven_zip_path))
                else:
                    patoolib.extract_archive(item_path, outdir=temp_folder, verbosity= -1, interactive=False, program=str(seven_zip_path))
                time.sleep(1)
                return True
            except PatoolError:
                print(f"{Bcolors.FAIL}The archive {base_item_name} can not be extracted{Bcolors.ENDC}")
                return False

# Removes everything in temp folder that is not one of the target folders before importing to library
def clean_folder(folder_path):
    targets = [folder for folder in target_folders]

    for item_path in pathlib.Path(folder_path).iterdir():
        item = item_path.name

        # If it's a folder and not in target folders, delete it
        if pathlib.Path(item_path).is_dir() and item not in targets:
            shutil.rmtree(item_path)

        # If it's a file, delete it
        elif pathlib.Path(item_path).is_file():
            pathlib.Path(item_path).unlink()

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
                if is_debug_mode:
                    pathlib.Path(str(root)).joinpath(file)
                    patoolib.extract_archive(str(pathlib.Path(str(root)).joinpath(file)), outdir=str(root), verbosity=2,
                                             interactive=False, program=str(seven_zip_path))
                else:
                    patoolib.extract_archive(str(pathlib.Path(str(root)).joinpath(file)), outdir=str(root), verbosity=-1,
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
            shutil.copytree(root, library_path, dirs_exist_ok=True)
            return True
    return False

def start_installer_gui(file_path, is_delete_archive=False):

    with lock:
        create_temp_folder()
        clean_temp_folder()
        if not extract_archive(file_path, is_debug_mode):
            clean_temp_folder()
            return
        if traverse_directory(temp_folder, pathlib.Path(file_path), is_debug_mode):
            print(f"{Bcolors.OKGREEN}{file_path} was successfully imported to your library{Bcolors.ENDC}")
        else:
            print(f"{Bcolors.WARNING}{file_path} can not be automatically imported because it doesn't have the right folder structure{Bcolors.ENDC}")
            print(f"{Bcolors.WARNING}or the archive already exists in the database{Bcolors.ENDC}")
        clean_temp_folder()
        delete_temp_folder()
        if is_delete_archive:
            pathlib.Path(file_path).unlink()