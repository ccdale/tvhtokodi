#
# Copyright (c) 2023, Chris Allison
#
#     This file is part of tvhtokodi.
#
#     tvhtokodi is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     tvhtokodi is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with tvhtokodi.  If not, see <http://www.gnu.org/licenses/>.
import json
import os
import shutil
import sys
import types
from signal import SIGINT, signal
from threading import Event

import ccalogging
import daemon
from ccalogging import log

import tvhtokodi
from tvhtokodi import errorExit, errorNotify, errorRaise
from tvhtokodi.files import dirFileList, makeFileList, splitfn
from tvhtokodi.tvh import deleteRecording

# log = None

ev = Event()
ev.clear()


def interruptWD(signrcvd: int, frame: types.FrameType) -> None:
    try:
        global ev
        msg = "Keyboard interrupt received in move module - exiting."
        log.info(msg)
        ev.set()
        # sys.exit(255)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


# if we get a `ctrl-c` from the keyboard or a kill -15, stop immediately
# by going to the interruptWD above
signal(SIGINT, interruptWD)



def moveShow(show: dict) -> None:
    try:
        failed = False
        deletelist = []
        copylist = []
        log.info(f"Moving {show['title']}")
        log.debug(f"Creating / Using directory: {show['destination']}")
        os.makedirs(show["destination"], exist_ok=True, mode=0o755)
        files = makeFileList(show["filename"])
        for f in files:
            pdir, pbase, pext = splitfn(f)
            if pext != ".ts":
                deletelist.append(f)
            # ddir, dbase, dext = splitfn(show["destfn"])
            # dext = ".ts" if not show["destfn"].endswith(".ts") else ""
            dbase = (
                show["destfn"][:-3]
                if show["destfn"].endswith(".ts")
                else show["destfn"]
            )
            dest = os.path.join(show["destination"], f"{dbase}{pext}")
            log.debug(f"Moving {f} to {dest}")
            shutil.copy(f, dest)
            copylist.append(dest)
        for f in copylist:
            log.debug(f"checking {dest}")
            if not os.path.exists(f):
                log.error(f"Copy Failure: Unable to find {f}")
                failed = True
                continue
        if not failed:
            log.info("writing NFO")
            dest = os.path.join(show["destination"], f"{dbase}.nfo")
            log.debug(f"Writing nfo to {dest}")
            with open(dest, "w") as ofn:
                ofn.write(show["nfo"])
            log.info(f"Deleting from TVHeadend {show['title']}")
            deleteRecording(show["uuid"])
            for f in deletelist:
                if os.path.exists(f):
                    log.debug(f"Deleting {f}")
                    os.remove(f)
                else:
                    log.error(f"Unable to find deletable file {f}")
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def moveShows(shows: list[dict]) -> None:
    try:
        label = "shows" if len(shows) > 1 else "show"
        log.info(f"Moving {len(shows)} {label}")
        for show in shows:
            moveShow(show)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def doMove(fqfn: str) -> None:
    try:
        # setupLog(stream=sys.stdout)
        # log.info(f"{tvhtokodi.__appname__}: {tvhtokodi.__version__} starting")
        # tvhtokodi.readConfig()
        # fqfn = os.path.abspath(os.path.expanduser("~/.tvhincoming/tvhtokodi-move.json"))
        if os.path.exists(fqfn):
            with open(fqfn, "r") as ifn:
                shows = json.load(ifn)
                moveShows(shows)
            log.debug(f"Removing {fqfn}")
            os.remove(fqfn)
            log.info("All done.")
        else:
            log.info("Nothing to do at this time for {fqfn} does not exist.")
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def filesList() -> list[str]:
    try:
        incomingpath = os.path.abspath(os.path.expanduser(tvhtokodi.cfg["destination"]))
        fns = dirFileList(incomingpath)
        jfns = [f for f in fns if f.endswith(".json")]
        return jfns
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def watchDir() -> None:
    try:
        log.info("inside watchDir")
        log.debug(f"{tvhtokodi.cfg=}")
        log.debug(
            f"{tvhtokodi.__appname__} watch dir {tvhtokodi.__version__} starting to watch {tvhtokodi.cfg['destination']}"
        )
        while not ev.is_set():
            fns = filesList()
            for f in fns:
                fqfn = os.path.join(tvhtokodi.cfg["destination"], f)
                doMove(fqfn)
            ev.wait(int(tvhtokodi.cfg["watchinterval"]))
        log.debug(f"{tvhtokodi.__appname__} watch dir {tvhtokodi.__version__} completed.")
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def daemonDirWatch() -> None:
    try:
        with daemon.DaemonContext():
            logfile = os.path.abspath(
                os.path.expanduser(f"~/log/{tvhtokodi.__appname__}-watchdir.log")
            )
            ccalogging.setLogFile(logfile)
            # ccalogging.setDebug()
            ccalogging.setInfo()
            log = ccalogging.log
            log.info(f"{tvhtokodi.__appname__}: {tvhtokodi.__version__} starting")
            log.debug(f"{tvhtokodi.__appname__}-watchdir deamonised!")
            tvhtokodi.readConfig()
            watchDir()
            log.info(f"{tvhtokodi.__appname__}: {tvhtokodi.__version__} exiting")
    except Exception as e:
        errorExit(sys.exc_info()[2], e)


if __name__ == "__main__":
    daemonDirWatch()
