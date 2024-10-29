import sys
import os
import time
import shutil
import configparser

from patoolib.util import PatoolError
import patoolib

import patches # Needed to apply monkey patching


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

if not library_path or library_path == "Y:\\example":
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

def clean_temp_folder():
    shutil.rmtree(temp_folder)
    os.makedirs(temp_folder)

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

def clean_folder():
    targets = [folder for folder in target_folders]

    # Walk through the directory
    for item in os.listdir(temp_folder):
        item_path = os.path.join(temp_folder, item)

        # If it's a folder and not in target folders, delete it
        if os.path.isdir(item_path) and item not in targets:
            shutil.rmtree(item_path)
            print(f"Deleted folder: {item_path}")

        # If it's a file, delete it
        elif os.path.isfile(item_path):
            os.remove(item_path)
            print(f"Deleted file: {item_path}")


def traverse_directory(folder_path):
    archive_extracted = False
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(('.zip', '.rar', '7z', '.tar')):
                patoolib.extract_archive(os.path.join(str(root), file), outdir=root, verbosity= -1, interactive=False)
                time.sleep(0.5)
                os.remove(os.path.join(root, file))
                archive_extracted = True
        if archive_extracted:
            return traverse_directory(folder_path)
        if any(target in dirs for target in target_folders):
            clean_folder()
            shutil.copytree(root, library_path, dirs_exist_ok=True)
            return True
    return False

clean_temp_folder()
for current_item in os.listdir(download_folder):
    if not extract_archive(current_item):
        clean_temp_folder()
        continue
    if traverse_directory(temp_folder):
        print(f"{Bcolors.OKGREEN}{current_item} was successfully imported to your library{Bcolors.ENDC}")
    else:
        print(f"{Bcolors.WARNING}{current_item} can not be automatically imported because it doesn't have the right folder structure{Bcolors.ENDC}")
        print(f"{Bcolors.WARNING}You need to do it manually{Bcolors.ENDC}")
    clean_temp_folder()
