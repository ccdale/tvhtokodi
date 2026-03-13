
from fabric import Connection

from tvhtokodi import errorNotify
from tvhtokodi.config import expandPath, readConfig, writeConfig


def remoteCommand(cmd, banner=False):
    """run a command on the media server"""
    try:
        cfg = readConfig()
        mhost = cfg["tvhhost"]
        muser = cfg["tvhuser"]
        mkeyfn = expandPath(f'~/.ssh/{cfg["keyfn"]}')
        ckwargs = {"key_filename": mkeyfn}
        if banner:
            print(f"Running remote command on {mhost}: {cmd}", flush=True)
        with Connection(host=mhost, user=muser, connect_kwargs=ckwargs) as c:
            result = c.run(cmd, hide=True)
            if result.exited == 0:
                return result.stdout.strip()
            else:
                return ""
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        return ""