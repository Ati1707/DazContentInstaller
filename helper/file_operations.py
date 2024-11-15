from pathlib import Path, PurePath
import shutil


def get_file_from_path(file_path):
    return PurePath(file_path).name

def get_file_name_without_extension(file):
    return file.rpartition(".")[0]

def create_folder() -> bool:
    """Also returns a boolean to check if it's a users first time starting the tool"""
    if not Path.exists(Path("database/")):
        Path.mkdir(Path("database/"))
        return True

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