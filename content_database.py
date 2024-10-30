import os
import sqlite3
import configparser
import time
from pick import pick

KEY_CTRL_C = 3
QUIT_KEYS = (KEY_CTRL_C, ord("q"))

config = configparser.ConfigParser()
config.read("config.ini")
library_path = config["PATH"]["LibraryPath"]

# Function to add a new archive and its files
def add_archive(archive_name, files):
    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO archives (archive_name) VALUES (?)", (archive_name,))
    archive_id = cursor.lastrowid
    cursor.executemany("INSERT INTO files (archive_id, file_name) VALUES (?, ?)",
                       [(archive_id, file_name) for file_name in files])
    conn.commit()
    print(f"Archive '{archive_name}' with {len(files)} files added.")

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
    return archive_list

# Function to delete an archive and its associated files
def delete_archive(archive_name):
    conn = connect_database()
    cursor = conn.cursor()
    # Retrieve the archive ID and associated files
    cursor.execute("SELECT id FROM archives WHERE archive_name = ?", (archive_name,))
    result = cursor.fetchone()

    if result:
        archive_id = result[0]

        # Get all files associated with the archive
        cursor.execute("SELECT file_name FROM files WHERE archive_id = ?", (archive_id,))
        files = cursor.fetchall()

        # Loop through and print the files to be deleted
        if files:
            for file in files:
                file_path = os.path.join(library_path, file[0])
                print(file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)  # Delete the file


        # Delete the archive (this will also delete associated files due to ON DELETE CASCADE)
        cursor.execute("DELETE FROM archives WHERE id = ?", (archive_id,))
        conn.commit()

        print(f"Archive '{archive_name}' and its files have been deleted.")
    else:
        print(f"Archive '{archive_name}' not found.")


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
                return True
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

def start_database():
    title = "Press space to select an or multiple assets and press enter to confirm your selection\nPress q to quit"
    options = get_archives()
    selected = pick(options, title, multiselect=True, min_selection_count=1, indicator="=>", quit_keys=QUIT_KEYS)
    for archive in selected:
        archive_name = archive[0][0]
        delete_archive(archive_name)
    print("Exiting tool....")
    time.sleep(3)