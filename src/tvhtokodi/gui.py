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
"""GUI module for tvhtokodi."""
import sys

import PySimpleGUI as sg

import tvhtokodi
from tvhtokodi import errorNotify
from tvhtokodi.recordings import recordedTitles


def displayTitles(titles):
    try:
        tvhkodi.readConfig()
        layout = [
            [sg.Text("Titles")],
            [sg.Listbox(titles.keys())],
        ]
        wind = sg.Window("TVHeadend Recordings", layout)
        while True:
            event, values = wind.read()
            if event == sg.WIN_CLOSED or event == "Exit":
                break
        wind.close()
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


if __name__ == "__main__":
    recs, titles = recordedTitles()
    displayTitles(titles)
