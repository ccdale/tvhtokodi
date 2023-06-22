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
"""Config module for tvhtokodi application"""
import json
from pathlib import Path
import sys

import tvhtokodi
from tvhtokodi import __appname__, errorExit

configfn = Path.home().joinpath(".config", f"{__appname__}.json")


def writeConfig(config):
    try:
        with open(str(configfn), "w") as ofn:
            json.dump(config, ofn)
    except Exception as e:
        errorExit(sys.exc_info()[2], e)


def readConfig():
    try:
        config = {}
        with open(str(configfn), "r") as ifn:
            config = json.load(ifn)
        return config
    except Exception as e:
        errorExit(sys.exc_info()[2], e)


def setConfig():
    try:
        cfg = readConfig()
        tvhtokodi.tvhuser = cfg["tvhuser"]
        tvhtokodi.tvhpass = cfg["tvhpass"]
        tvhtokodi.tvhipaddr = cfg["tvhipaddr"]
        return cfg
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
