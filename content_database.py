import pathlib
import sqlite3
import threading
from helper.config_operations import get_library_path


lock = threading.Lock()

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

            print(f"Archive '{archive_name}' and its files have been deleted.")
        else:
            print(f"Archive '{archive_name}' not found.")
        conn.close()


def archive_exist(archive_name, file_list):
    conn = connect_database()
    cursor = conn.cursor()
    # Get the number of files to check against
    file_count = len(file_list)

    # Query to check if an archive with the same number of files exists
    cursor.execute('''
        SELECT a.archive_name FROM archives a
        JOIN files f ON a.id = f.archive_id
        GROUP BY a.id
        HAVING COUNT(f.id) = ?
    ''', (file_count,))

    existing_archives = cursor.fetchall()

    # Check if the specific archive_name already exists with the same file count
    if existing_archives:
        for existing_archive in existing_archives:
            if existing_archive[0] == archive_name:
                print(f"An archive named '{archive_name}' with {file_count} files already exists.")
                conn.close()
                return True
    conn.close()
    return False

def connect_database():
    conn = sqlite3.connect('database/archives.db')
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    conn.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS archives (
            id INTEGER PRIMARY KEY,
            archive_name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            archive_id INTEGER,
            file_name TEXT NOT NULL,
            FOREIGN KEY (archive_id) REFERENCES archives (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    return conn