import logging
import shutil

from datetime import datetime
from pathlib import Path, PurePath


def get_file_from_path(file_path):
    return PurePath(file_path).name


def get_file_name_without_extension(file):
    return file.rpartition(".")[0]


def create_folder(folder_path: str) -> None:
    """
    Creates a folder if it does not already exist.

    Args:
        folder_path (str): The path to the folder.
    """
    folder = Path(folder_path)
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)


def create_database_folder() -> bool:
    """
    Creates the 'database/' folder if it doesn't exist.

    Returns:
        bool: True if the folder was created (indicating first-time use), False otherwise.
    """
    database_path = Path("database/")
    if not database_path.exists():
        database_path.mkdir(parents=True, exist_ok=True)
        return True
    return False


def create_log_folder() -> None:
    create_folder("logs/")


def create_temp_folder() -> None:
    create_folder("temp/")


def delete_temp_folder() -> None:
    temp_path = Path("temp/")
    if temp_path.exists():
        shutil.rmtree(temp_path)


def get_file_size(file_path):
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return _convert_size(file.stat().st_size)


def _convert_size(size_bytes: int) -> str:
    """
    Converts a file size in bytes to a human-readable format.

    Args:
        size_bytes (int): The file size in bytes.

    Returns:
        str: The file size in human-readable format (e.g., KB, MB).
    """
    if size_bytes == 0:
        return "0 B"

    size_units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_units) - 1:
        size_bytes /= 1024
        i += 1

    return f"{size_bytes:.2f} {size_units[i]}"


def limit_logger_files() -> None:
    """
    Deletes the oldest log files when the number of log files exceeds the limit.
    """
    log_dir = Path("logs/")

    log_files = sorted(log_dir.iterdir(), key=lambda f: f.stat().st_ctime)

    if len(log_files) > 2:
        files_to_delete = len(log_files) - 2
        for file in log_files[:files_to_delete]:
            file.unlink()


def create_logger() -> logging.Logger:
    """
    Sets up the logging configuration and creates a new log file.

    Returns:
        logging.Logger: A configured logger instance.
    """
    create_log_folder()
    limit_logger_files()
    now = datetime.now().strftime("%d.%m.%Y %H-%M-%S")
    log_file = Path("logs") / f"{now}.log"
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S",
    )
    return logging.getLogger(__name__)


def is_file_archive(file):
    if file.lower().endswith((".zip", ".rar", ".7z", ".tar")):
        return True
