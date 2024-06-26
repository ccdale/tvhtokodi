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
import os
import sys
import textwrap

import PySimpleGUI as sg

import tvhtokodi
from tvhtokodi import errorNotify
from tvhtokodi.recordings import recordedTitles
from tvhtokodi.nfo import hmsDisplay, makeProgNfo, makeFilmNfo
from tvhtokodi.files import sendFileTo

log = None


def displayTitles(titles):
    try:
        op = []
        sent = []
        ignored = tvhtokodi.cfg["ignoretitles"]
        names = sorted([n for n in titles])
        names = refreshNames(names, sent)
        titleslist = sg.Listbox(
            names,
            size=(60, 40),
            enable_events=True,
            key="-TLIST-",
        )
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
                    dest, seriesfolders, nfo = progWindow(
                        titles[selection[0]][0], len(titles[selection[0]])
                    )
                    if dest:
                        for title in titles[selection[0]]:
                            title["destfn"], title["destination"] = decideDestFn(
                                title, dest, seriesfolders
                            )
                            title["nfo"] = nfo
                            op.append(title)
                        sendNextFile(op)
                        sent.append(op[0]["title"])
                    op = []
                    ignored = tvhtokodi.cfg["ignoretitles"]
                    names = refreshNames(names, sent)
                    wind["-TLIST-"].update(values=names)
                    log.debug(f"{selection[0]=}")
        wind.close()
        # return op
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def refreshNames(names, sent):
    try:
        ignored = tvhtokodi.cfg["ignoretitles"]
        for n in sent:
            if n in names:
                names.remove(n)
        for n in ignored:
            if n in names:
                names.remove(n)
        return names
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def decideDestFn(title, xdest, seriesfolders):
    try:
        dest = xdest
        if seriesfolders == "FILM":
            destfn = f"{os.path.basename(title['filename'])}"
        elif seriesfolders and title["season"] and title["episode"]:
            dest = f"{xdest}Series {title['season']:0>2}/"
            destfn = f"{title['title']} - S{title['season']:0>2}E{title['episode']:0>2}"
        elif seriesfolders and title["season"]:
            dest = f"{xdest}Series {title['season']:0>2}/"
            destfn = f"{title['title']}"
        elif title["season"] and title["episode"]:
            destfn = f"{title['title']} - S{title['season']:0>2}E{title['episode']:0>2}"
        elif title["extratext"]:
            destfn = f"{title['title']} - {title['extratext']}"
        else:
            destfn = f"{os.path.basename(title['filename'])}"
        return destfn, dest
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def progWindow(show, total=1):
    try:
        log.debug(f"{show=}")
        filmdir = tvhtokodi.cfg["filmdir"]
        tvdir = tvhtokodi.cfg["tvdir"]
        dests = ["Comedy", "Documentary", "Drama", "Music"]
        nfo = None
        desc = show["description"]
        if len(desc) > 80:
            tmp = textwrap.wrap(desc)
            desc = "\n".join(tmp)
        msg = f"{total} programme" if total == 1 else f"{total} programmes"
        # legend = "Move" if total == 1 else f"Move {total} Programmes"
        legend = f"Move {msg}"
        checked = True if show["season"] and show["episode"] else False
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
                    sg.Checkbox(
                        "Series Folders", key="-SERIESFOLDERS-", default=checked
                    ),
                ]
            ],
            [
                [
                    sg.Button(legend, key="-MOVE-"),
                    sg.Button("Ignore Show", key="-IGNORE-"),
                    sg.Cancel(),
                ]
            ],
        ]
        wind = sg.Window(show["title"], layout)
        seriesfolders = False
        while True:
            event, values = wind.read()
            if event in (sg.WIN_CLOSED, "Exit", "Quit"):
                dest = None
                break
            if event == "-IGNORE-":
                ignoreShow(show["title"])
                dest = None
                seriesfolders = False
                nfo = None
                break
            if event == "-MOVE-":
                if values["-YEAR-"] == "Year":
                    cat = values["-DEST-"]
                    dest = f"{tvdir}/{cat}/{show['title']}/"
                    seriesfolders = values["-SERIESFOLDERS-"]
                    nfo = makeProgNfo(show)
                else:
                    dest = f"{filmdir}/{show['title'][:1].upper()}/{show['title']} ({values['-YEAR-']})/"
                    seriesfolders = "FILM"
                    show["year"] = values["-YEAR-"]
                    nfo = makeFilmNfo(show)
                log.debug(f"{dest=}")
                break
        log.debug(f"{event=}\n{values=}")
        wind.close()
        return dest, seriesfolders, nfo
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def ignoreShow(title):
    try:
        tvhtokodi.cfg["ignoretitles"].append(title)
        tvhtokodi.writeConfig()
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def sendNextFile(move):
    try:
        fnum = int(tvhtokodi.cfg["filenumber"])
        opfn = f"/tmp/tvhtokodi-move-{fnum}.json"
        with open(opfn, "w") as ofn:
            json.dump(move, ofn, indent=4)
        sendFileTo(opfn)
        if fnum == 99:
            fnum = 0
        tvhtokodi.cfg["filenumber"] = f"{fnum + 1}"
        tvhtokodi.writeConfig()
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def doGui():
    try:
        global log
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
        # move = displayTitles(titles)
        displayTitles(titles)
        # log.debug(f"{move=}")
        # sendNextFile(move)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


if __name__ == "__main__":
    doGui()
