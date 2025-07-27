import json
import os
import sys

import tvhtokodi
from tvhtokodi import errorExit, errorNotify, errorRaise
from tvhtokodi.films import displayFilms
from tvhtokodi.nfo import hmsDisplay, makeFilmNfo, makeProgNfo
from tvhtokodi.recordings import recordedTitles


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


def main():
    try:
        op = []
        sent = []
        tvhtokodi.readConfig()
        recs, titles = recordedTitles()
        displayFilms(recs)
        # with open("titles.json", "w") as f:
        #     json.dump(titles, f, indent=4)
        # sys.exit(0)
        # films = findFilms(recs)
        # for cn, film in enumerate(films, 1):
        #     ex = ""
        #     if "copyright_year" in film:
        #         ex = f" ({film['copyright_year']})"
        #     print(f"{cn:>3} {film['disp_title']}{ex} ({hmsDisplay(film['duration'])})")
        # i = input("\nEnter the number of the film to not send to Kodi, or press Enter to send all: ")
        # if i:
        #     try:
        #         i = int(i)
        #         if i < 1 or i > len(films):
        #             raise ValueError("Invalid number")
        #     except ValueError as e:
        #         errorExit(f"Invalid input: {e}")
        #     notsent = [films[i - 1]["disp_title"]]
        #     films.pop(i - 1)
        # with open("recs.json", "w") as f:
        #     json.dump(recs, f, indent=4)
        # ignored = tvhtokodi.cfg["ignoretitles"]
        # names = sorted([n for n in titles])
        # names = refreshNames(names, sent)
        # print("\n".join(names))
    except Exception as e:
        errorExit(f"tvhtokodi enncountered an error: {e}")


if __name__ == "__main__":
    main()
