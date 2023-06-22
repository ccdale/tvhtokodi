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
"""Test module for the tvhtokodi.tvh module"""

# import json
import sys

# import pytest

import tvhtokodi
from tvhtokodi.config import setConfig
from tvhtokodi.tvh import allRecordings, sendToTvh, TVHError

# setup the tvh auth config before testing
cfg = setConfig()


def test_sendToTvh():
    route = "dvr/entry/grid_finished"
    data = {"limit": 100}
    jdat = sendToTvh(route, data=data)
    assert "total" in jdat


def test_allRecordings():
    recordings, total = allRecordings()
    assert len(recordings) == total
