import json
import urllib.request
import webbrowser

from packaging.version import Version

api_url = "https://api.github.com/repos/Ati1707/DazContentInstaller/releases/latest"


def is_new_update_available(local_version):
    response = urllib.request.urlopen(api_url).read()
    data = json.loads(response)

    latest_version = data["tag_name"].strip("v")

    if Version(latest_version) > Version(local_version):
        return True
    return False


def open_release_page():
    webbrowser.open(
        "https://github.com/Ati1707/DazContentInstaller/releases", new=0, autoraise=True
    )
