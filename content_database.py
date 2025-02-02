import logging
import sqlite3
import threading
from pathlib import Path

from helper.config_operations import get_library_path, get_debug_mode

lock = threading.Lock()


def connect_database(db_path: str = "database/archives.db") -> sqlite3.Connection:
    """Connect to the SQLite database and ensure necessary tables exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS archives (
                id INTEGER PRIMARY KEY,
                archive_name TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                archive_id INTEGER,
                file_name TEXT NOT NULL,
                FOREIGN KEY (archive_id) REFERENCES archives (id) ON DELETE CASCADE
            )
        """)
    return conn


def add_archive(archive_name: str, files: list[str]) -> None:
    """
    Add a new archive and its associated files to the database.

    Args:
        archive_name (str): The name of the archive.
        files (List[str]): A list of file names to associate with the archive.
    """
    with connect_database() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO archives (archive_name) VALUES (?)", (archive_name,)
            )
            archive_id = cursor.lastrowid
            cursor.executemany(
                "INSERT INTO files (archive_id, file_name) VALUES (?, ?)",
                [(archive_id, file_name) for file_name in files],
            )
            logging.info(f"Archive '{archive_name}' added with {len(files)} files.")
        except sqlite3.IntegrityError:
            logging.error(f"Archive '{archive_name}' already exists. Skipping.")


def get_archives() -> list[tuple[str, str]]:
    """
    Retrieve a list of all archives and their file counts.

    Returns:
        list[tuple[str, str]]: A list of tuples containing the archive name and file count.
    """
    with connect_database() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, archive_name FROM archives")
        archives = cursor.fetchall()

        archive_list = []
        for archive_id, archive_name in archives:
            cursor.execute(
                "SELECT COUNT(*) FROM files WHERE archive_id = ?", (archive_id,)
            )
            file_count = cursor.fetchone()[0]
            archive_list.append((archive_name, f"{file_count} files"))

        return archive_list


def delete_archive(archive_name: str) -> None:
    """
    Delete an archive and its associated files from the database and filesystem.

    Args:
        archive_name (str): The name of the archive to delete.
    """
    with lock:  # Ensure thread safety
        with connect_database() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM archives WHERE archive_name = ?", (archive_name,)
            )
            result = cursor.fetchone()

            if not result:
                logging.info(f"Archive '{archive_name}' not found.")
                return

            archive_id = result[0]
            cursor.execute(
                "SELECT file_name FROM files WHERE archive_id = ?", (archive_id,)
            )
            files = cursor.fetchall()

            # Delete associated files from the filesystem
            for (file_name,) in files:
                file_path = Path(get_library_path()) / file_name
                try:
                    if file_path.exists():
                        file_path.unlink()
                        if get_debug_mode():
                            logging.info(f"Deleted file: {file_path}")
                except Exception as e:
                    logging.error(f"Error deleting file {file_path}: {e}")

            # Delete the archive and its entries in the database
            cursor.execute("DELETE FROM archives WHERE id = ?", (archive_id,))
            logging.info(f"Archive '{archive_name}' and its files have been deleted.")


def does_archive_exist(archive_name: str) -> bool:
    """
    Check if an archive exists in the database by name only.
    """
    with connect_database() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM archives WHERE archive_name = ?)",
            (archive_name,),
        )
        return cursor.fetchone()[0] == 1
