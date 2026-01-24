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
import sys
from pathlib import Path

import tomllib

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

def gitroot() -> str:
    """
    Get the root directory of the current git repository.
    Returns:
        str: Path to the root directory of the git repository.
    """
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True
            )  # noqa: E501
            .splitlines()
            .pop()
        )
    except Exception as e:
        errorExit(sys.exc_info()[2], e)
        return ""


def getProjectData() -> dict:
    """
    Get the project data from pyproject.toml.
    Returns:
        dict: The project data.
    """
    try:
        git_root = gitroot()
        if not git_root:
            return {}
        pyproject_path = Path(git_root) / "pyproject.toml"
        if not pyproject_path.exists():
            return {}
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        return pyproject_data.get("project", {})
    except Exception as e:
        errorExit(sys.exc_info()[2], e)


def getVersion() -> str:
    """
    Get the version of the project from pyproject.toml.
    Returns:
        str: The version string.
    """
    try:
        pyproject_data = getProjectData()
        return pyproject_data.get("version", "0.0.0")
    except Exception as e:
        errorExit(sys.exc_info()[2], e)

def getAppName() -> str:
    """
    Get the application name from pyproject.toml.
    Returns:
        str: The application name.
    """
    try:
        pyproject_data = getProjectData()
        return pyproject_data.get("name", "tvhtokodi")
    except Exception as e:
        errorExit(sys.exc_info()[2], e)

__version__ = getVersion()
__appname__ = getAppName()