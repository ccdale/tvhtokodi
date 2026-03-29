import sys
from io import StringIO
from pathlib import Path

from fabric import Connection

import tvhtokodi
from tvhtokodi import errorNotify, expandPath
from tvhtokodi.files import humanSize
from tvhtokodi.tvh import TVHError


def remoteCommand(cmd: str, banner: bool = False, failok: bool = False) -> str:
    """run a command on the media server"""
    try:
        mhost = tvhtokodi.cfg["sshhost"]
        muser = tvhtokodi.cfg["sshuser"]
        mkeyfn = expandPath(f'~/.ssh/{tvhtokodi.cfg["keyfn"]}')
        ckwargs = {"key_filename": mkeyfn}
        if banner:
            print(f"Running remote command on {mhost}: {cmd}", flush=True)
        with Connection(host=mhost, user=muser, connect_kwargs=ckwargs) as c:
            result = c.run(cmd, hide=False, warn=failok)
            if result.exited == 0:
                return result.stdout.strip()
            else:
                if failok:
                    return ""
                else:
                    raise TVHError(f"remote command failed: {cmd}")
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return ""

def allShowFiles(show: dict, banner: bool = False) -> list[str]:
    """get a list of all files associated with a show on the media server"""
    try:
        showdir = Path(show["filename"]).parent
        stub = Path(show["filename"]).stem
        findcmd = f'ls -1 "{showdir}/{stub}"* 2>/dev/null || true'
        res = remoteCommand(findcmd, banner=banner)
        return res.split("\n") if res else []
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return []

def cpRemoteFile(src: str, dest: str, banner: bool = False) -> bool:
    """copy a file on the media server"""
    try:
        cpCmd = f'cp "{src}" "{dest}"'
        result = remoteCommand(cpCmd, banner=banner)
        return result == ""
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return False



def remoteFileSize(fn: str, human: bool = False) -> int:
    """get the size of a file on the media server"""
    try:
        res = remoteCommand(f'stat -c%s "{fn}"')
        if res:
            return humanSize(int(res)) if human else int(res)
        else:
                return -1
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return -1

def remoteExists(fn: str, isdir: bool = False) -> bool:
    """check if a file exists on the media server"""
    try:
        checkcmd = f'test -f "{fn}" && ls "{fn}"' if not isdir else f'test -d "{fn}" && ls "{fn}"'
        res = remoteCommand(checkcmd, failok=True)
        # returns True if string is not empty (i.e. the 'ls' succeeded), False if string is empty (i.e. the 'ls' failed)
        return res != ""
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return False

def remoteFinalFileName(src: str) -> str:
    """ensure that the remote final file name does not exist, adding a suffix if needed"""
    try:
        basedir = Path(src).parent
        base_name = Path(src).stem
        prefix = f"{basedir}/{base_name}" if basedir != "" else base_name
        ext = Path(src).suffix
        cn = 0
        fexists = True
        while fexists:
            if cn == 0:
                test_name = f"{prefix}{ext}"
            else:
                test_name = f"{prefix}-{cn}{ext}"
            checkcmd = f'test -f "{test_name}"'
            res = remoteCommand(checkcmd, failok=True)
            if res != "":
                cn += 1
            else:
                fexists = False
                return test_name
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return src

def remoteSHA256(fn: str) -> str:
    """get the sha256 hash of a file on the media server"""
    try:
        res = remoteCommand(f'sha256sum "{fn}"', failok=True)
        if res:
            return res.split()[0]
        else:
            return ""
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return ""

def remoteMkdir(dir: str) -> bool:
    """make a directory on the media server"""
    try:
        mkdirCmd = f'mkdir -p "{dir}"'
        result = remoteCommand(mkdirCmd, failok=True)
        return result == ""
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return False

def copyTVFiles(srcfiles: list[str], destdir: str, banner: bool = False) -> bool:
    """copy a list of files on the media server to a destination directory"""
    try:
        if remoteExists(destdir, isdir=True):
            if banner:
                print(f"Destination directory {destdir} already exists on media server")
            return False
        if remoteMkdir(destdir):
            for src in srcfiles:
                srcsize = remoteFileSize(src)
                destfn = remoteFinalFileName(f"{destdir}/{Path(src).name}")
                if banner:
                    print(f"Copying {src} to {destfn} on media server")
                cpCmd = f'cp "{src}" "{destfn}"'
                result = remoteCommand(cpCmd, banner=banner)
                if result != "":
                    return False
                destsize = remoteFileSize(destfn)
                if srcsize != destsize:
                    if banner:
                        print(f"Size mismatch after copying {src} to {destfn} on media server: {srcsize} != {destsize}")
                    return False
            return True
        return False
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return False


def remoteWriteTextFile(destfn: str, content: str, banner: bool = False) -> bool:
    """write text content to a file on the media server via Fabric/SSH"""
    try:
        mhost = tvhtokodi.cfg["sshhost"]
        muser = tvhtokodi.cfg["sshuser"]
        mkeyfn = expandPath(f'~/.ssh/{tvhtokodi.cfg["keyfn"]}')
        ckwargs = {"key_filename": mkeyfn}

        if not remoteMkdir(str(Path(destfn).parent)):
            return False

        if banner:
            print(f"Writing remote text file {destfn} on {mhost}", flush=True)

        with Connection(host=mhost, user=muser, connect_kwargs=ckwargs) as c:
            c.put(StringIO(content), destfn)

        return remoteExists(destfn)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return False