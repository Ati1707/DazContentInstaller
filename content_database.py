import logging
import pathlib
import sqlite3
import threading
from typing import Tuple

from helper.config_operations import get_library_path


lock = threading.Lock()

def connect_database(db_path: str = "database/archives.db") -> sqlite3.Connection:
    """Connect to the SQLite database and ensure necessary tables exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS archives (
                id INTEGER PRIMARY KEY,
                archive_name TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                archive_id INTEGER,
                file_name TEXT NOT NULL,
                FOREIGN KEY (archive_id) REFERENCES archives (id) ON DELETE CASCADE
            )
        ''')
    return conn

# Function to add a new archive and its files
def add_archive(archive_name, files):
    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO archives (archive_name) VALUES (?)", (archive_name,))
    archive_id = cursor.lastrowid
    cursor.executemany("INSERT INTO files (archive_id, file_name) VALUES (?, ?)",
                       [(archive_id, file_name) for file_name in files])
    conn.commit()
    conn.close()

# Function to retrieve all archives and their files
def get_archives():
    conn = connect_database()
    cursor = conn.cursor()
    archive_list = []
    cursor.execute("SELECT * FROM archives")
    archives = cursor.fetchall()
    for archive in archives:
        archive_id, archive_name = archive
        cursor.execute("SELECT file_name FROM files WHERE archive_id = ?", (archive_id,))
        files = cursor.fetchall()
        archive_list.append((archive_name, str(len(files)) + " files" ))
    conn.close()
    return archive_list


# Function to delete an archive and its associated files
def delete_archive(archive_name):
    with lock:
        logger = logging.getLogger(__name__)
        conn = connect_database()
        cursor = conn.cursor()
        # Retrieve the archive ID and associated files
        cursor.execute("SELECT id FROM archives WHERE archive_name = ?", (archive_name,))
        result = cursor.fetchone()

        if result:
            archive_id = result[0]

            cursor.execute("SELECT file_name FROM files WHERE archive_id = ?", (archive_id,))
            files = cursor.fetchall()
            # Loop through and print the files to be deleted
            if files:
                for file in files:
                    file_path = pathlib.Path(get_library_path()).joinpath(file[0])
                    if pathlib.Path(file_path).exists():
                        pathlib.Path(file_path).unlink()

            # Delete the archive (this will also delete associated files due to ON DELETE CASCADE)
            cursor.execute("DELETE FROM archives WHERE id = ?", (archive_id,))
            conn.commit()

            logger.info(f"Archive '{archive_name}' and its files have been deleted.")
        else:
            logger.info(f"Archive '{archive_name}' not found.")
        conn.close()


def does_archive_exist(archive_name: str, file_list: list[str]) -> bool:
    """
    Check if an archive exists in the database with the same name and file count.

    Args:
        archive_name (str): The name of the archive to check.
        file_list (List[str]): The list of files to compare against.

    Returns:
        bool: True if an archive with the same name and file count exists, False otherwise.
    """
    file_count = len(file_list)
    with connect_database() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT COUNT(*) FROM archives a
            JOIN files f ON a.id = f.archive_id
            WHERE a.archive_name = ?
            GROUP BY a.id
            HAVING COUNT(f.id) = ?
            ''',
            (archive_name, file_count),
        )
        result = cursor.fetchone()
        return result is not None