import sys
import os
import time
import shutil
import configparser
import re
import patoolib

from patoolib.util import PatoolError

import content_database
import patches # Needed to apply monkey patching

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

if not os.path.exists(download_folder):
    os.makedirs(download_folder)
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

config = configparser.ConfigParser()
config.read("config.ini")
library_path = config["PATH"]["LibraryPath"]

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
    os.makedirs(temp_folder)

# Extract archives in the download folder and move content to temp folder
def extract_archive(item):
        item_path = os.path.join(download_folder, item)
        if item.endswith(('.zip', '.rar', '7z', '.tar')):
            print(f"Extracting: {item}")
            try:
                patoolib.extract_archive(item_path, outdir=temp_folder, verbosity= -1, interactive=False)
                time.sleep(1)
                return True
            except PatoolError:
                print(f"{Bcolors.FAIL}The archive {item} can not be extracted{Bcolors.ENDC}")
                return False

# Removes everything in temp folder that is not one of the target folders before importing to library
def clean_folder(folder_path):
    targets = [folder for folder in target_folders]

    for item in os.listdir(folder_path):
        item_path = os.path.join(temp_folder, item)

        # If it's a folder and not in target folders, delete it
        if os.path.isdir(item_path) and item not in targets:
            shutil.rmtree(item_path)

        # If it's a file, delete it
        elif os.path.isfile(item_path):
            os.remove(item_path)

def add_to_database(root_path, item):
    archive_name = item.split(".")[0]
    file_list = []

    # Traverse through all files in the directory
    for item in os.listdir(root_path):
        for root, dir, files in os.walk(os.path.join(root_path, item)):
            if files:
                for file in files:
                    file_list.append(os.path.join(get_relative_path(root), file))
    if content_database.archive_exist(archive_name, file_list):
        return True
    print(f"Archive '{archive_name}' added to the database with {len(file_list)} files.")
    content_database.add_archive(archive_name, file_list)
    time.sleep(1)


# Searching the content of extracted archive for target folders
def traverse_directory(folder_path, current_item):
    archive_extracted = False
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(('.zip', '.rar', '7z', '.tar')):
                patoolib.extract_archive(os.path.join(str(root), file), outdir=root, verbosity= -1, interactive=False)
                time.sleep(0.5)
                os.remove(os.path.join(root, file))
                archive_extracted = True
        if archive_extracted:
            return traverse_directory(folder_path, current_item)
        if any(target in dirs for target in target_folders):
            clean_folder(root)
            if add_to_database(root, current_item):
                return False
            shutil.copytree(root, library_path, dirs_exist_ok=True)
            return True
    return False

def start_installer():
    clean_temp_folder()
    for current_item in os.listdir(download_folder):
        if not extract_archive(current_item):
            clean_temp_folder()
            continue
        if traverse_directory(temp_folder, current_item):
            print(f"{Bcolors.OKGREEN}{current_item} was successfully imported to your library{Bcolors.ENDC}")
        else:
            print(
                f"{Bcolors.WARNING}{current_item} can not be automatically imported because it doesn't have the right folder structure{Bcolors.ENDC}")
            print(f"{Bcolors.WARNING}or the archive already exists in the database{Bcolors.ENDC}")
        clean_temp_folder()

    print("Finished importing every asset")
    print("Tool exiting in 3 seconds....")
    time.sleep(3)
