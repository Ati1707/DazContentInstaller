import os
import shutil


def get_file_from_path(file_path):
    return os.path.basename(file_path)

def split_file_and_extension(file):
    return file.rpartition(".")[0], file.rpartition(".")[-1]

def create_folders():
    if not os.path.exists("database/"):
        os.makedirs("database/")
    if not os.path.exists("downloads/"):
        os.makedirs("downloads/")

def create_temp_folder():
    if not os.path.exists("temp/"):
        os.makedirs("temp/")

def delete_temp_folder():
    if os.path.exists("temp/"):
        shutil.rmtree("temp/")