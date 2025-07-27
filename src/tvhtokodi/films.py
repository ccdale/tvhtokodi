import json
import os
import sys

from tabulate import tabulate

import tvhtokodi
from tvhtokodi import errorExit, errorNotify, errorRaise
from tvhtokodi.files import sendFileTo
from tvhtokodi.nfo import hmsDisplay


def listItems(items, xkey="disp_title"):
    try:
        rows = []
        for cn, item in enumerate(items, 1):
            ex = ""
            if "copyright_year" in item:
                ex = f"{item['copyright_year']}"
            dur = hmsDisplay(item.get("duration", 0))
            row = [cn, item[xkey], ex, dur]
            rows.append(row)
        print(tabulate(rows))
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def findFilms(recs):
    try:
        films = []
        for rec in recs:
            if "duration" not in rec:
                continue
            elif rec["duration"] > 4500:  # 75 minutes
                if "copyright_year" in rec and rec["copyright_year"] > 1900:
                    films.append(rec)
            elif "category" in rec:
                for cat in rec["category"]:
                    if cat.lower() == "feature film" or cat.lower() == "movie":
                        films.append(rec)
                        break

        return films
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def displayFilms(recs):
    try:
        films = findFilms(recs)
        if not films:
            raise Exception("No films found in recordings.")
        films.sort(key=lambda x: x.get("copyright_year", 0))
        filmdir = tvhtokodi.cfg["filmdir"]
        for film in films:
            # print(f"{film=}")
            title = film.get("disp_title", "Unknown Title")
            initial = titleInitial(title)
            year = film.get("copyright_year", 0)
            film["destination"] = f"{filmdir}/{initial}/{title} ({year})/"
            print(f"film dest: {film['destination']}")
            film["destfn"] = f"{os.path.basename(film['filename'])}"
            print(f"film destfn: {film['destfn']}")
            print(f"Film Source: {film['filename']}")
            # sendNextFile([film])
            print()
    except Exception as e:
        errorExit(sys.exc_info()[2], e)


def filmMenu(film, films, choice_index):
    try:
        print(f"Film Menu for: {film['disp_title']}")
        choice = input("(I)gnore, Enter to go back: ").lower()
        if choice == "i":
            print(f"Ignoring {film['disp_title']}.")
            films.pop(choice_index)
        return films
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


def titleInitial(title):
    try:
        tmp = title.split(" ")
        first = tmp[0].lower()
        if "a" == first or "the" == first:
            first = tmp[1].lower()
        return first[:1].upper()
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
