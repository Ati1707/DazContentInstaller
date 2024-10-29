import os
import time
from pick import pick
from content_database import start_database
from installer import start_installer

KEY_CTRL_C = 3
QUIT_KEYS = (KEY_CTRL_C, ord("q"))

def main():
    title = 'Please select an option.\nPress q to exit'
    options = ["1. Start the installer", "2. Delete an asset from the library"]
    option, index = pick(options, title,indicator="=>", quit_keys=QUIT_KEYS)
    match index:
        case 0:
            start_installer()
        case 1:
            try:
                start_database()
            except ValueError:
                print("The database is empty. Restarting tool")
                time.sleep(2)
                os.system("cls")
                main()



if __name__ == "__main__":
    main()