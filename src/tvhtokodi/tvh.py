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
"""tvh module for tvhtokodi"""

import json
import sys

import requests

import tvhtokodi
from tvhtokodi import errorNotify


class TVHError(Exception):
    pass


def sendToTvh(route: str, data: dict = None) -> dict:
    """Send a request to tvheadend"""
    try:
        # print(f"current config: {tvhtokodi.cfg}", flush=True)
        auth = (tvhtokodi.cfg["tvhuser"], tvhtokodi.cfg["tvhpass"])
        url = f"http://{tvhtokodi.cfg['tvhipaddr']}/api/{route}"
        # print(f"Requesting {url} with params {data}", flush=True)
        r = requests.get(url, params=data, auth=auth)
        # print(f"Response: {r.status_code} {r.text}", flush=True)
        if r.status_code != 200:
            raise TVHError(f"error communicating with tvh: {r}")
        return r.json()
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        try:
            print("Error decoding json from tvh, trying again", flush=True)
            txt = r.text.replace(chr(25), " ")
            return json.loads(txt)
        except Exception as xe:
            errorNotify(sys.exc_info()[2], xe)


def allRecordings() -> tuple[list[dict], int]:
    try:
        route = "dvr/entry/grid_finished"
        data = {"limit": 9999}
        jdat = sendToTvh(route, data=data)
        return jdat["entries"], jdat["total"]
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def deleteRecording(uuid: str) -> None:
    try:
        data = {"uuid": uuid}
        sendToTvh("dvr/entry/remove", data)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
