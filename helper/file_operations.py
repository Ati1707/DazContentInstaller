import logging
import shutil

from datetime import datetime
from pathlib import Path, PurePath



def get_file_from_path(file_path):
    return PurePath(file_path).name

def get_file_name_without_extension(file):
    return file.rpartition(".")[0]

def create_database_folder() -> bool:
    """Also returns a boolean to check if it's a users first time starting the tool"""
    if not Path.exists(Path("database/")):
        Path.mkdir(Path("database/"))
        return True

def create_log_folder():
    if not Path.exists(Path("logs/")):
        Path.mkdir(Path("logs/"))

def create_temp_folder():
    if not Path.exists(Path("temp/")):
        Path.mkdir(Path("temp/"))

def delete_temp_folder():
    if Path.exists(Path("temp/")):
        shutil.rmtree("temp/")

def get_file_size(file_path):
    return _convert_size(Path(file_path).stat().st_size)

def _convert_size(size_bytes):
    # Edge case for size 0 bytes
    if size_bytes == 0:
        return "0 B"

    # List of size units
    size_units = ["B", "KB", "MB", "GB"]
    i = 0

    # Convert to larger units until size is below 1024
    while size_bytes >= 1024 and i < len(size_units) - 1:
        size_bytes /= 1024
        i += 1

    # Return formatted size with 2 decimal places
    return f"{size_bytes:.2f} {size_units[i]}"

def limit_logger_files():
    """Function to delete the oldest log file when there are already 3 present"""
    log_dir = Path("logs/")
    log_files = list(log_dir.iterdir())  # Get all files in the directory

    if len(log_files) > 2:
        # Sort files by creation time (ascending order, oldest first)
        log_files_sorted = sorted(log_files, key=lambda f: f.stat().st_ctime)

        # Delete the oldest files to ensure only 2 are kept
        files_to_delete = len(log_files) - 2
        for file in log_files_sorted[:files_to_delete]:
            print(f"Deleting: {file}")
            file.unlink()

def create_logger():
    create_log_folder()
    limit_logger_files()
    now = datetime.now()
    now = now.strftime("%d.%m.%Y %H-%M-%S")
    log_file = f"logs/{now}.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%m/%d/%Y %I:%M:%S'
    )
    return logging.getLogger(__name__)
