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
import json
import logging
import sys
import textwrap

import PySimpleGUI as sg

import tvhtokodi
from tvhtokodi import errorNotify
from tvhtokodi.recordings import recordedTitles
from tvhtokodi.nfo import hmsDisplay
from tvhtokodi.files import sendFileTo


def displayTitles(titles):
    try:
        op = []
        names = [n for n in titles]
        titleslist = sg.Listbox(
            names,
            size=(60, 40),
            # expand_x=True,
            # expand_y=True,
            enable_events=True,
            key="-TLIST-",
        )
        # slist = sg.Listbox(
        #     ["one", "two", "three"], size=(60, 40), enable_events=True, key="-SLIST-"
        # )
        layout = [
            [sg.Text("Titles")],
            [sg.Text(f"Total Titles: {len(titles)}")],
            [titleslist],
            [sg.Quit()],
        ]
        wind = sg.Window("TVHeadend Recordings", layout)
        # tlist = wind["-TLIST-"]
        while True:
            event, values = wind.read()
            log.debug(f"event: {event}\nvalues: {values}")
            if event in (sg.WIN_CLOSED, "Exit", "Quit"):
                break
            elif event == "-TLIST-":
                selection = values[event]
                log.debug(f"{selection=}")
                if selection:
                    dest, seriesfolders = progWindow(
                        titles[selection[0]][0], len(titles[selection[0]])
                    )
                    if dest:
                        for title in titles[selection[0]]:
                            title["destination"] = dest
                            title["seriesfolders"] = seriesfolders
                            op.append(title)
                    log.debug(f"{selection[0]=}")
                    # log.debug(f"{tlist.get_indexes()[0]=}")
        wind.close()
        return op
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def progWindow(show, total=1):
    try:
        log.debug(f"{show=}")
        dests = ["Comedy", "Documentary", "Drama", "Music"]
        desc = show["description"]
        if len(desc) > 80:
            tmp = textwrap.wrap(desc)
            desc = "\n".join(tmp)
        msg = f"{total} programme" if total == 1 else f"{total} programmes"
        legend = "Move" if total == 1 else f"Move {total} Programmes"
        layout = [
            [sg.Text(f'{show["ctimestart"]} Duration: {hmsDisplay(show["duration"])}')],
            [sg.Text(show["title"])],
            [sg.Text(msg)],
            [sg.Text(show["subtitle"])],
            [sg.Text(desc)],
            [sg.Text(f"Season: {show['season']} Episode: {show['episode']}")],
            [
                [
                    sg.Combo(dests, key="-DEST-"),
                    sg.Input("Year", key="-YEAR-"),
                    sg.Checkbox("Series Folders", key="-SERIESFOLDERS-"),
                ]
            ],
            [[sg.Button(legend, key="-MOVE-"), sg.Quit()]],
        ]
        wind = sg.Window(show["title"], layout)
        seriesfolders = False
        while True:
            event, values = wind.read()
            if event in (sg.WIN_CLOSED, "Exit", "Quit"):
                dest = None
                break
            if event == "-MOVE-":
                if values["-YEAR-"] == "Year":
                    cat = values["-DEST-"]
                    dest = f"TV/{cat}/{show['title']}/"
                    seriesfolders = values["-SERIESFOLDERS-"]
                else:
                    dest = f"films/{show['title'][:1].lower()}/{show['title']} ({values['-YEAR-']})/"
                log.debug(f"{dest=}")
                break
        log.debug(f"{event=}\n{values=}")
        wind.close()
        return dest, seriesfolders
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def doGui():
    try:
        cformat = "%(asctime)s [%(levelname)-5.5s]  %(message)s"
        datefmt = "%d/%m/%Y %H:%M:%S"
        cfmt = logging.Formatter(cformat, datefmt=datefmt)
        consH = logging.StreamHandler(sys.stderr)
        consH.setFormatter(cfmt)
        log = logging.getLogger(tvhtokodi.__appname__)
        log.addHandler(consH)
        log.setLevel(logging.DEBUG)
        tvhtokodi.readConfig()
        recs, titles = recordedTitles()
        move = displayTitles(titles)
        log.debug(f"{move=}")
        opfn = "/tmp/tvhtokodi-move.json"
        with open(opfn, "w") as ofn:
            json.dump(move, ofn, indent=4)
        sendFileTo(opfn)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


if __name__ == "__main__":
    doGui()
