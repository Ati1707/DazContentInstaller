import configparser


def get_library_path():
    config = _get_config_file()
    return config["PATH"].get("LibraryPath").strip('"')


def get_debug_mode():
    config = _get_config_file()
    return config["DEBUG"].getboolean("DebugMode")


def _get_config_file():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config
