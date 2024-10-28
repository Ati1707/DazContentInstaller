import os
import patoolib
import shutil
import configparser
import time

config = configparser.ConfigParser()

config.read("config.ini")

library_path = config["PATH"]["LibraryPath"]

download_folder = 'downloads/'  # Change this to your specific folder
temp_folder = 'temp/'

if not os.path.exists(download_folder):
    os.makedirs(download_folder)

if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

# Define the target folders
target_folders = [
    "aniBlocks", "data", "Environments", "Light Presets", "People",
    "Props", "ReadMe's", "Render Presets", "Render Settings", "Runtime",
    "Scenes", "Scripts", "Shader Presets"
]



# Specify the base folder to start extracting from

def extract_all_archives():
    for item in os.listdir(download_folder):
        item_path = os.path.join(download_folder, item)
        if item.endswith(('.zip', '.rar')):
            print(f"Extracting: {item_path}")
            patoolib.extract_archive(item_path, outdir=temp_folder, verbosity= -1)
            #time.sleep(0.5)


def extract_archives(folder_path):
    for root, dirs, files in os.walk(folder_path):
        if any(target in root for target in target_folders):
            continue
        for target in dirs:
            if target in target_folders:
                target_path = os.path.join(root, target)
                if not any(target_path.startswith(f"temp/{folder}") for folder in target_folders):
                    shutil.copytree(root, folder_path, dirs_exist_ok=True)
                    shutil.rmtree(root)
                    return extract_archives(folder_path)

        for file in files:
            file_path = os.path.join(root, file)

            # Check for zip and rar files
            if file.endswith(('.zip', '.rar')):
                print(f'Extracting {file_path}')
                patoolib.extract_archive(file_path, outdir=root, verbosity= -1)
                #time.sleep(0.2)
                os.remove(file_path)  # Delete the archive


def clean_directory(directory_path):
    # Ensure target_folders are treated as absolute paths for comparison
    target_folders_set = set(target_folders)

    # Traverse the directory
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)

        # Check if the item is a directory
        if os.path.isdir(item_path):
            # Remove the directory if it's not a target folder
            if item not in target_folders_set:
                print(f'Removing directory: {item_path}')
                shutil.rmtree(item_path)
        else:
            # Remove the file if it's not in a target folder
            print(f'Removing file: {item_path}')
            os.remove(item_path)

def import_to_library():
    for item in os.listdir(temp_folder):
        item_path = os.path.join(temp_folder, item)
        dest_path = os.path.join(library_path, item)
        shutil.move(item_path, dest_path)
        print(f'Moved {item_path} to {dest_path}')

extract_all_archives()
extract_archives(temp_folder)
clean_directory(temp_folder)
import_to_library()
