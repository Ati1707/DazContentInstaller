# Daz Content Installer
WINDOWS ONLY!  

DazContentInstaller is a user-friendly tool designed to simplify the process of extracting archives, as well as installing and removing assets. It addresses the issue where third-party assets sometimes lack the proper structure for importing with the DAZ Install Manager.

## Usage

You can either get the [Release](https://github.com/Ati1707/DazContentInstaller/releases) or clone the repository and install the requirements to run the main file with Python:

1. You can either drag and drop your archives or add them with the button below
2. If an archive cannot be imported, you will receive a warning or an error. You need to manually import those if the archive is not corrupt.
3. To remove an asset from the library switch to the Uninstall tab

## Debug mode

To use the debug mode, open the config.ini and change the DebugMode value to true

## Credits

[https://www.7-zip.org/](https://www.7-zip.org) using their console tool  
[patool](https://github.com/wummel/patool) for extracting archives  
[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) library used for the GUI  
[Messagebox Widget](https://github.com/Akascape/CTkMessagebox) custom messagebox widget  
[Tooltip Widget](https://github.com/Akascape/CTkToolTip) custom tooltip widget  
[Pywinstyles](https://github.com/Akascape/py-window-styles) to enable the drag and drop feature  
[PyInstaller](https://github.com/pyinstaller/pyinstaller) to create the binary
## Screenshot

![Screnshot](https://github.com/user-attachments/assets/50b5b1c3-a2aa-4de1-83e8-56f28c339d2a)
