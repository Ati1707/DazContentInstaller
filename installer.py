import pathlib
import patoolib
import re
import shutil
import sqlite3
import threading
import time
from helper.config_operations import get_library_path, get_debug_mode
from helper.file_operations import create_temp_folder, delete_temp_folder, create_logger
from patoolib.util import PatoolError
from PySide6.QtCore import QMutex
import content_database
import patches

install_mutex = QMutex()

# Create a logger instance
logger = create_logger()
# Path to the temporary extraction folder
TEMP_FOLDER = pathlib.Path("temp")

# Folders to target during extraction
TARGET_FOLDERS = [
    "aniBlocks",
    "data",
    "Environments",
    "Light Presets",
    "People",
    "Props",
    "ReadMe's",
    "Render Presets",
    "Render Settings",
    "Runtime",
    "Scenes",
    "Scripts",
    "Shader Presets",
    "Cameras",
    "Documentation",
]

# Path to the 7z executable
SEVEN_ZIP_PATH = str(pathlib.Path(__file__).parent.absolute() / "7z") + "\\7z.exe"

# Create a threading lock
lock = threading.Lock()

archive_exists = False


def get_relative_path(full_path: str) -> str:
    """
    Get the relative path based on target folders.
    If the path contains a target folder, return the sub-path starting
    from the target folder.
    """
    pattern = r"|".join([re.escape(folder) for folder in TARGET_FOLDERS])
    match = re.search(pattern, full_path)
    return full_path[match.start() :] if match else full_path


def clean_temp_folder() -> None:
    """
    Clean the temporary folder by removing its contents.
    """
    if TEMP_FOLDER.exists():
        shutil.rmtree(TEMP_FOLDER)
    TEMP_FOLDER.mkdir(parents=True, exist_ok=True)


def extract_archive(item_path: pathlib.Path, is_debug_mode: bool) -> bool:
    """
    Extract an archive into the temporary folder.
    """
    base_item_name = item_path.name
    if base_item_name.lower().endswith((".zip", ".rar", ".7z", ".tar")):
        logger.info(f"Extracting {base_item_name}")
        try:
            verbosity = 2 if is_debug_mode else -1
            patoolib.extract_archive(
                str(item_path),
                outdir=str(TEMP_FOLDER),
                verbosity=verbosity,
                interactive=False,
                program=str(SEVEN_ZIP_PATH),
            )
            time.sleep(1)
            return True
        except PatoolError as e:
            logger.error(f"Failed to extract archive {base_item_name}: {e}")
            return False
    return False


def clean_folder(folder_path: pathlib.Path) -> None:
    """
    Remove all files in the specified folder.
    """
    for item in folder_path.iterdir():
        if item.is_file():
            item.unlink()


def add_to_database(root_path: pathlib.Path, item: pathlib.Path) -> bool:
    """
    Add files to database after confirming unique name (already checked earlier)
    """
    archive_name = item.stem.split(".")[0]
    file_list = [
        get_relative_path(str(file_path))
        for file_path in root_path.rglob("*")
        if file_path.is_file()
    ]

    try:
        logger.info(f"Adding archive '{archive_name}' with {len(file_list)} files.")
        content_database.add_archive(archive_name, file_list)
        time.sleep(1)
        return False
    except sqlite3.IntegrityError:
        logger.warning(f"Archive '{archive_name}' already exists (race condition)")
        return True


def handle_nested_archives(root_path, files, is_debug_mode):
    """
    Handle and extract nested archives within the main archive.
    """
    archive_extracted = False
    for file in files:
        file_path = root_path / file
        if file.lower().endswith((".zip", ".rar", ".7z", ".tar")):
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
    return archive_extracted


def process_manifest_and_target_folders(root_path, dirs, files, current_item):
    """
    Check for manifest files and target folders, and process them accordingly.
    """
    manifest_exists = any(file.lower().endswith("manifest.dsx") for file in files)

    if manifest_exists or any(target in dirs for target in TARGET_FOLDERS):
        for folder in dirs:
            if manifest_exists and folder.lower().startswith("content"):
                content_path = root_path / folder
                clean_folder(content_path)
                if add_to_database(content_path, current_item):
                    return False
                shutil.copytree(content_path, get_library_path(), dirs_exist_ok=True)
                return True

            if any(target.lower() == folder.lower() for target in TARGET_FOLDERS):
                clean_folder(root_path)
                if add_to_database(root_path, current_item):
                    return False
                shutil.copytree(root_path, get_library_path(), dirs_exist_ok=True)
                return True
    return False


def traverse_directory(
    folder_path: pathlib.Path,
    current_item: pathlib.Path,
    is_debug_mode: bool,
):
    """
    Traverse the directory structure and handle nested archives and target folders.
    """
    for root, dirs, files in folder_path.walk():
        root_path = pathlib.Path(root)

        if handle_nested_archives(root_path, files, is_debug_mode):
            return traverse_directory(folder_path, current_item, is_debug_mode)
        if process_manifest_and_target_folders(root_path, dirs, files, current_item):
            return True
        if archive_exists:
            return False

    return False


def start_installer_gui(
    file_path: str, progress_callback, is_delete_archive: bool = False
) -> tuple[bool, bool]:
    is_archive_imported = False
    file_path = pathlib.Path(file_path)
    install_mutex.lock()
    try:
        logger.info(f"Installing {file_path}")

        # Get archive name from file path
        archive_name = file_path.stem.split(".")[0]  # Handle double extensions

        # Early check before any processing
        if content_database.does_archive_exist(archive_name):
            logger.warning(f"Asset already exists: {archive_name}")
            progress_callback(100)  # Immediate completion
            return False, True  # (not imported, already exists)

        create_temp_folder()
        clean_temp_folder()
        progress_callback(10)

        if not extract_archive(file_path, get_debug_mode()):
            clean_temp_folder()
            delete_temp_folder()
            progress_callback(100)
            return False, False

        progress_callback(40)

        # Simplified processing since we already checked existence
        traversal_success = traverse_directory(TEMP_FOLDER, file_path, get_debug_mode())
        if traversal_success:
            is_archive_imported = True
            logger.info(f"Successfully imported: {file_path}")

        clean_temp_folder()
        delete_temp_folder()
        progress_callback(90)

        if is_delete_archive:
            try:
                file_path.unlink()
                logger.info(f"Deleted archive: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete archive {file_path}: {e}")

        progress_callback(100)
        return is_archive_imported, False
    finally:
        install_mutex.unlock()
