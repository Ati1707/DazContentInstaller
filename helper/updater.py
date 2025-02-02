import json
import urllib.request
import webbrowser

from packaging.version import Version
from helper.file_operations import create_logger

api_url = "https://api.github.com/repos/Ati1707/DazContentInstaller/releases/latest"
logger = create_logger()

def is_new_update_available(local_version):
    try:
        response = urllib.request.urlopen(api_url).read()
        data = json.loads(response)
        latest_version = data["tag_name"].strip("v")
        return Version(latest_version) > Version(local_version)
    except Exception as e:
        # Handle any HTTP or network-related errors here
        logger.warning(f"Could not check for updates. Reason: {e}")
        return False



def open_release_page():
    webbrowser.open(
        "https://github.com/Ati1707/DazContentInstaller/releases", new=0, autoraise=True
    )
