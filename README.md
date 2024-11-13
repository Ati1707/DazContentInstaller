# DazContentInstaller
WINDOWS ONLY!  

DazContentInstaller is a user-friendly tool designed to simplify the process of extracting archives, as well as installing and removing assets. It addresses the issue where third-party assets sometimes lack the proper structure for importing with the DAZ Install Manager.

The 7-Zip binary is included in the repository without any modifications. It has been directly sourced from [https://www.7-zip.org/](https://www.7-zip.org)  

The tool only supports zip, rar, tar and 7z archives at the moment  
More can be added if needed but I only encountered these

## Usage

You can either get the [Release](https://github.com/Ati1707/DazContentInstaller/releases) or clone the repository and install the requirements to run the main file with Python:

1. Start the binary once to generate the necessary folders.
2. Change the library path in the config file or use the placeholder path (DO NOT USE YOUR MAIN LIBRARY FILE; THIS TOOL IS NOT STABLE YET!).
3. Place the downloaded assets in the downloads folder (the assets must be archives; everything else will be ignored).
4. If an archive cannot be imported, you will receive a warning or an error. You will need to manually import it if the archive is not corrupted.

After the content is imported, you can delete the archives in the downloads folder.

## Debug mode
To use the debug mode, open the config.ini and change the DebugMode value to true

## Showcase(Outdated)

<video src="https://github.com/user-attachments/assets/5170f047-99c4-4373-a2e8-0dd8b0640c3a"/>
