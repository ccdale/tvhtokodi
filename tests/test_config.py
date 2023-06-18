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
"""Test module for tvhtokodi.config module"""

import pytest

from tvhtokodi.config import readConfig, writeConfig


def test_ReadConfig():
    cfg = readConfig()
    assert cfg["tvhuser"] == "chris-admin"


def test_WriteConfig(capsys):
    cfg = readConfig()
    writeConfig(cfg)
    out, err = capsys.readouterr()
    assert err == ""