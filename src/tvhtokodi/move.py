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
import logging
import os
import shutil
import sys

import tvhtokodi
from tvhtokodi import errorNotify
from tvhtokodi.files import makeFileList, splitfn
from tvhtokodi.tvh import deleteRecording

log = None


def setupLog(stream=sys.stderr):
    try:
        global log
        cformat = "%(asctime)s [%(levelname)-5.5s]  %(message)s"
        datefmt = "%d/%m/%Y %H:%M:%S"
        cfmt = logging.Formatter(cformat, datefmt=datefmt)
        consH = logging.StreamHandler(stream)
        consH.setFormatter(cfmt)
        log = logging.getLogger(tvhtokodi.__appname__)
        log.addHandler(consH)
        log.setLevel(logging.DEBUG)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def moveShow(show):
    try:
        failed = False
        deletelist = []
        log.info(f"Moving {show['title']}")
        log.debug(f"Creating / Using directory: {show['destination']}")
        os.makedirs(show["destination"], exist_ok=True, mode=0o755)
        files = makeFileList(show["filename"])
        for f in files:
            pdir, pbase, pext = splitfn(f)
            if pext != ".ts":
                deletelist.append(f)
            # ddir, dbase, dext = splitfn(show["destfn"])
            dext = ".ts" if not show["destfn"].endswith(".ts") else ""
            dbase = (
                show["destfn"][:-3]
                if show["destfn"].endswith(".ts")
                else show["destfn"]
            )
            dest = os.path.join(show["destination"], f"{dbase}{dext}")
            log.debug(f"Moving {f} to {dest}")
            shutil.copy(f, dest)
        for f in files:
            log.debug(f"checking {dest}")
            if not os.path.exists(dest):
                log.error(f"Copy Failure: Unable to find {dest}")
                failed = True
                continue
        if not failed:
            log.info(f"Deleting from TVHeadend {show['title']}")
            # deleteRecording(show["uuid"])
            for f in deletelist:
                log.debug(f"Deleting {f}")
                os.remove(f)
            log.info("writing NFO")
            dest = os.path.join(show["destination"], f"{dbase}.nfo")
            log.debug(f"Writing nfo to {dest}")
            with open(dest, "w") as ofn:
                ofn.write(show["nfo"])
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def moveShows(shows):
    try:
        label = "shows" if len(shows) > 1 else "show"
        log.info(f"Moving {len(shows)} {label}")
        for show in shows:
            moveShow(show)
            break
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def doMove():
    try:
        setupLog(stream=sys.stdout)
        log.info(f"{tvhtokodi.__appname__}: {tvhtokodi.__version__} starting")
        tvhtokodi.readConfig()
        fqfn = os.path.abspath(os.path.expanduser("~/.tvhincoming/tvhtokodi-move.json"))
        if os.path.exists(fqfn):
            with open(fqfn, "r") as ifn:
                shows = json.load(ifn)
                moveShows(shows)
            log.debug(f"Removing {fqfn}")
            os.remove(fqfn)
            log.info("All done.")
        else:
            log.info("Nothing to do at this time.")
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


if __name__ == "__main__":
    doMove()
