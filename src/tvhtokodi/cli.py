import sys

import tvhtokodi
from tvhtokodi import errorExit, errorRaise
from tvhtokodi.films import displayFilms
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
        tvhtokodi.readConfig()
        recs, titles = recordedTitles()
        displayFilms(recs)
    except Exception as e:
        errorExit(f"tvhtokodi enncountered an error: {e}")


if __name__ == "__main__":
    main()
