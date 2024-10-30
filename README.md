# DazContentInstaller
WINDOWS ONLY!  

DazContentInstaller is a user-friendly tool designed to simplify the process of extracting archives,  installing and removing assets since sometimes third party assets don't have the right structure to be imported with the DAZ install manager.


7-Zip is included in the repo.  
No changes were made the standalone version got directly pulled from [https://www.7-zip.org/](https://www.7-zip.org)  

The tool only supports zip, rar, tar and 7z archives at the moment  
More can be added if needed but I only encountered these

## Usage

You can either get the [Release](https://github.com/Ati1707/DazContentInstaller/releases)  
Or clone the repo and install the requirements to run the main file with python

1. Change library path in the config file or use the placeholder one(DO NOT USE YOUR MAIN LIBRARY FILE THIS TOOL IS NOT STABLE YET!!!!)  
2. Put the downloaded assets in the downloads folder(The assets must be archives everything else gets ignored)  
3. If an archive can't be imported you'll get a warning or an error. You need to manually import it if the archive is not corrupted.  


After the content got imported you can delete the archives in the downloads folder if they got successfully imported
