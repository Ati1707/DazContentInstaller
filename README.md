# Daz Content Installer
WINDOWS ONLY!  

DazContentInstaller is a user-friendly tool designed to simplify the process of extracting archives, as well as installing and removing assets. It addresses the issue where third-party assets sometimes lack the proper structure for importing with the DAZ Install Manager.

The 7-Zip binary is included in the repository without any modifications. It has been directly sourced from [https://www.7-zip.org/](https://www.7-zip.org)  

The tool only supports zip, rar, tar and 7z archives at the moment  
More can be added if needed but I only encountered these

## Usage

You can either get the [Release](https://github.com/Ati1707/DazContentInstaller/releases) or clone the repository and install the requirements to run the main file with Python:

1. Do not change the library path in the config.ini yet
2. You can either drag and drop your archives or add them with the button below
3. If an archive cannot be imported, you will receive a warning or an error in the console. You need to manually import those if the archive is not corrupt
4. If you want to remove an asset from the library switch to the Uninstall tab

## Debug mode
To use the debug mode, open the config.ini and change the DebugMode value to true

## Showcase

<video src="https://github.com/user-attachments/assets/5ced6e18-0abc-4f1a-8131-188aca18c99e"/>
