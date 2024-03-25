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
#
import json
from pathlib import Path
import sys


__version__ = "0.3.9"
__appname__ = "tvhtokodi"

configfn = Path.home().joinpath(".config", f"{__appname__}.json")
cfg = {}


def errorNotify(exci, e, fname=None):
    lineno = exci.tb_lineno
    if fname is None:
        fname = exci.tb_frame.f_code.co_name
    ename = type(e).__name__
    msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
    # log.error(msg)
    print(msg)


def errorRaise(exci, e, fname=None):
    errorNotify(exci, e, fname)
    raise


def errorExit(exci, e, fname=None):
    errorNotify(exci, e, fname)
    sys.exit(1)


def writeConfig():
    try:
        with open(str(configfn), "w") as ofn:
            json.dump(cfg, ofn, indent=4)
    except Exception as e:
        errorExit(sys.exc_info()[2], e)


def readConfig():
    try:
        global cfg
        with open(str(configfn), "r") as ifn:
            cfg = json.load(ifn)
    except Exception as e:
        errorExit(sys.exc_info()[2], e)
