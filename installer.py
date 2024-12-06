import logging
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
import content_database
import patches

logger = create_logger()

TEMP_FOLDER = pathlib.Path("temp")  # Temporary folder for extraction


lock = threading.Lock()

TARGET_FOLDERS = [
    "aniBlocks", "data", "Environments", "Light Presets", "People",
    "Props", "ReadMe's", "Render Presets", "Render Settings", "Runtime",
    "Scenes", "Scripts", "Shader Presets", "Cameras", "Documentation"
]

if getattr(sys, "frozen", False):
    BASE_PATH = pathlib.Path(sys._MEIPASS)
else:
    BASE_PATH = pathlib.Path(__file__).parent

SEVEN_ZIP_PATH = BASE_PATH / "7z/7z.exe"


def get_relative_path(full_path: str) -> str:
    """
    Extract the relative path starting from the first occurrence of a target folder.
    """
    pattern = r'|'.join([re.escape(folder) for folder in TARGET_FOLDERS])
    match = re.search(pattern, full_path)
    return full_path[match.start():] if match else full_path

def clean_temp_folder() -> None:
    """
    Clean and recreate the temporary folder.
    """
    if TEMP_FOLDER.exists():
        shutil.rmtree(TEMP_FOLDER)
    TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

def extract_archive(item_path: pathlib.Path, is_debug_mode: bool) -> bool:
    """
    Extract the archive to the temporary folder.
    """
    base_item_name = item_path.name
    if base_item_name.lower().endswith(('.zip', '.rar', '7z', '.tar')):
        logger.info(f"Extracting {base_item_name}")
        try:
            verbosity = 2 if is_debug_mode else -1
            patoolib.extract_archive(
                str(item_path),
                outdir=str(TEMP_FOLDER),
                verbosity=verbosity,
                interactive=False,
                program=str(SEVEN_ZIP_PATH)
            )
            time.sleep(1)
            return True
        except PatoolError as e:
            logger.error(f"Failed to extract archive {base_item_name}: {e}")
            return False
    return False

def clean_folder(folder_path: pathlib.Path) -> None:
    """
    Remove all files that are not part of the target folders.
    """
    for item in folder_path.iterdir():
        if item.is_file():
            item.unlink()

def add_to_database(root_path: pathlib.Path, item: pathlib.Path) -> bool:
    """
    Add the archive's content to the database.
    """
    archive_name = item.stem.split(".")[0]
    file_list = []

    # Collect all files in the directory
    for file_path in root_path.rglob("*"):
        if file_path.is_file():
            relative_path = get_relative_path(str(file_path))
            file_list.append(relative_path)

    if content_database.does_archive_exist(archive_name, file_list):
        logger.info(f"Archive '{archive_name}' already exists in the database.")
        return True
    else:
        logger.info(f"Adding archive '{archive_name}' with {len(file_list)} files to the database.")
        content_database.add_archive(archive_name, file_list)
        time.sleep(1)
        return False


# Searching the content of extracted archive for target folders
def traverse_directory(
    folder_path: pathlib.Path,
    current_item: pathlib.Path,
    progressbar,
    is_debug_mode: bool,
) -> bool:
    """
    Process a directory, search for nested archives, and add valid content to the library.

    Args:
        folder_path (pathlib.Path): The path of the folder to process.
        current_item (pathlib.Path): The current archive being processed.
        progressbar: A GUI progress bar object to track progress.
        is_debug_mode (bool): Whether debug mode is enabled for verbose logs.

    Returns:
        bool: True if the content was successfully added to the library, False otherwise.
    """
    archive_extracted = False
    manifest_exists = False

    # Traverse the directory structure
    for root, dirs, files in folder_path.walk():
        root_path = pathlib.Path(root)

        for file in files:
            file_path = root_path / file

            # Handle nested archives
            if file.lower().endswith(('.zip', '.rar', '7z', '.tar')):
                logger.info(f"Extracting nested archive: {file}")
                try:
                    verbosity = 2 if is_debug_mode else -1
                    patoolib.extract_archive(
                        str(file_path),
                        outdir=str(root_path),
                        verbosity=verbosity,
                        interactive=False,
                        program=str(SEVEN_ZIP_PATH),
                    )
                    time.sleep(0.5)
                    file_path.unlink()  # Delete the nested archive after extraction
                    archive_extracted = True
                except PatoolError as e:
                    logger.error(f"Failed to extract nested archive {file}: {e}")

            # Check for manifest files
            if file.lower().endswith("manifest.dsx"):
                manifest_exists = True

        progressbar.set(progressbar.get() + 0.1)

        # If a nested archive was extracted, restart traversal
        if archive_extracted:
            progressbar.set(progressbar.get() + 0.1)
            return traverse_directory(folder_path, current_item, progressbar, is_debug_mode, is_nested_archive=True)

        if manifest_exists:
            for folder in dirs:
                if folder.lower().startswith("content"):
                    content_path = root_path / folder
                    progressbar.set(0.9)
                    clean_folder(content_path)
                    if add_to_database(content_path, current_item):
                        return False
                    shutil.copytree(content_path, get_library_path(), dirs_exist_ok=True)
                    return True

        if any(target in dirs for target in TARGET_FOLDERS):
            progressbar.set(0.9)
            clean_folder(root_path)
            if add_to_database(root_path, current_item):
                return False
            shutil.copytree(root_path, get_library_path(), dirs_exist_ok=True)
            return True

    return False


def start_installer_gui(
    file_path: str, progressbar, is_delete_archive: bool = False
) -> bool:
    """
    Main function to handle the installation process via the GUI.

    Args:
        file_path (str): The path of the archive to process as a string.
        progressbar: A GUI progress bar object to track progress.
        is_delete_archive (bool): Whether to delete the archive after installation.

    Returns:
        bool: True if the archive was successfully imported, False otherwise.
    """
    is_archive_imported = False
    file_path = pathlib.Path(file_path)  # Convert the input string to a pathlib.Path object

    with lock:  # Ensure thread safety
        logger.info(f"Installing {file_path}")
        create_temp_folder()
        clean_temp_folder()
        progressbar.set(0.1)

        # Step 1: Extract the archive
        if not extract_archive(file_path, get_debug_mode()):
            clean_temp_folder()
            return is_archive_imported

        progressbar.set(0.4)

        # Step 2: Traverse the extracted directory
        if traverse_directory(TEMP_FOLDER, file_path, progressbar, get_debug_mode()):
            is_archive_imported = True
            logger.info(f"Successfully imported: {file_path}")
        else:
            is_archive_imported = False
            logger.warning(f"Failed to import {file_path}. Invalid folder structure or asset already exists.")

        # Cleanup
        clean_temp_folder()
        delete_temp_folder()

        # Step 3: Delete the original archive if requested
        if is_delete_archive:
            try:
                file_path.unlink()
                logger.info(f"Deleted archive: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete archive {file_path}: {e}")

        return is_archive_imported