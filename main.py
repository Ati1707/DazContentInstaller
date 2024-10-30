import os
import time
import sys
from pick import pick
from content_database import start_database
from installer import start_installer

KEY_CTRL_C = 3
QUIT_KEYS = (KEY_CTRL_C, ord("q"))

def main():
    if not os.path.isdir("downloads") or not os.path.isdir("database") or not os.path.isdir("temp"):
        print("Creating folders. Restarting tool...")
        create_folders()
        time.sleep(2)
        os.system("cls")
        return main()
    title = 'Please select an option.\nPress q to exit'
    options = ["1. Start the installer", "2. Delete an asset from the library"]
    option, index = pick(options, title,indicator="=>", quit_keys=QUIT_KEYS)
    match index:
        case 0:
            if len(sys.argv) > 1 and sys.argv[1].lower() == "debug":
                start_installer(True)
            else:
                start_installer()
        case 1:
            try:
                start_database()
            except ValueError:
                print("The database is empty. Restarting tool")
                time.sleep(2)
                os.system("cls")
                return main()

def create_folders():
    if not os.path.exists("database/"):
        os.makedirs("database/")
    if not os.path.exists("downloads/"):
        os.makedirs("downloads/")
    if not os.path.exists("temp/"):
        os.makedirs("temp/")



if __name__ == "__main__":
    main()