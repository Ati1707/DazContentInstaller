from patoolib.mime import *
from patoolib.util import *

def patched_run_checked(cmd, ret_ok=(0,), **kwargs):
    """Run command and raise PatoolError on error with an additional condition."""
    retcode = run(cmd, **kwargs)

    # Original condition, with an added condition:
    # Add a custom check, if retcode is not a specific value.
    if retcode not in ret_ok and retcode != 255:
        msg = f"Command `{cmd}' returned non-zero exit status {retcode}"
        raise PatoolError(msg)

    return retcode

def patched_guess_mime_file(filename: str) -> tuple[str | None, str | None]:
    """Determine MIME type of filename with file(1):
     (a) using `file --brief --mime-type`
     (b) using `file --brief` and look at the result string
     (c) detect compressed archives (eg. .tar.gz) using
         `file --brief --mime --uncompress --no-sandbox`
    @return: tuple (mime, encoding)
    """
    mime, encoding = None, None
    base, ext = os.path.splitext(filename)
    if ext.lower() in ('.alz',):
        # let mimedb recognize these extensions
        return mime, encoding
    if os.path.isfile(filename):
        file_prog = find_program("file")
        if file_prog:
            mime, encoding = guess_mime_file_mime(file_prog, filename)
            if mime is None:
                mime = guess_mime_file_text(file_prog, filename)
                encoding = None
    if mime in Mime2Encoding:
        # try to look inside compressed archives
        cmd = [file_prog, "--brief", "--mime", "--uncompress", "--no-sandbox", filename]
        try:
            outparts = backtick(cmd).strip().split(";")
            mime2 = outparts[0].split(" ", 1)[0]
        except (OSError, subprocess.CalledProcessError) as err:
            log_warning(f"error executing {cmd}: {err}")
            mime2 = None
        # Some file(1) implementations return an empty or unknown mime type
        # when the uncompressor program is not installed, other
        # implementation return the original file type.
        # The following detects both cases.
        if (
            mime2 in ('application/x-empty', 'application/octet-stream')
            or mime2 in Mime2Encoding
            or not mime2
        ):
            # The uncompressor program file(1) uses is not installed
            # or is not able to uncompress.
            # Try to get mime information from the file extension.
            mime2, encoding2 = guess_mime_mimedb(filename)
            if mime2 in ArchiveMimetypes:
                mime = mime2
                encoding = encoding2
        elif mime2 in ArchiveMimetypes:
            mime = mime2
            encoding = get_file_mime_encoding(outparts)
    return mime, encoding

def patched_run(cmd: Sequence[str], verbosity: int = 0, **kwargs) -> int:
    """Run command without error checking.
    @return: command return code
    """
    # Note that shell_quote_nt() result is not suitable for copy-paste
    # (especially on Unix systems), but it looks nicer than shell_quote().
    if verbosity >= 0:
        info = " ".join(map(shell_quote_nt, cmd))
        log_info(f"running {info}")
    if run_under_pythonw():
        # prevent opening of additional consoles when running with pythonw.exe
        kwargs["creationflags"] = (
            subprocess.CREATE_NO_WINDOW  # pytype: disable=module-attr
        )
    # try to prevent hangs for programs requiring input
    kwargs["input"] = ""
    if verbosity < 1:
        # hide command output on stdout
        kwargs['stdout'] = subprocess.DEVNULL
    if kwargs:
        if verbosity > 0:
            info = ", ".join(f"{k}={shell_quote(str(v))}" for k, v in kwargs.items())
            log_info(f"    with {info}")
        if kwargs.get("shell"):
            # for shell calls the command must be a string
            cmd = " ".join(cmd)
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    res = subprocess.run(cmd, startupinfo=startupinfo, **kwargs)
    return res.returncode

# Apply the patch
import patoolib

patoolib.util.run = patched_run
patoolib.util.run_checked = patched_run_checked
patoolib.mime.guess_mime_file = patched_guess_mime_file
