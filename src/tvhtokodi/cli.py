import sys

import tvhtokodi
from tvhtokodi import errorExit, errorRaise
from tvhtokodi.films import displayFilms
from tvhtokodi.recordings import recordedTitles
from tvhtokodi.remotefiles import copyTVFiles, remoteExists
from tvhtokodi.tvh import deleteRecording


def refreshNames(names: list, sent: list) -> list:
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
        print(f"{tvhtokodi.appname} version {tvhtokodi.version}")
        recs, titles = recordedTitles()
        films = displayFilms(recs)
        for film in films:
            print(f"moving {film['disp_title']} to kodi")
            if copyTVFiles(film["allfiles"], film["destination"], banner=True):
                print(f"successfully moved {film['disp_title']} to kodi")
                print("removing from tvheadend")
                deleteRecording(film["uuid"])
                alldeleted = True
                for f in film["allfiles"]:
                    if remoteExists(f):
                        print(f"file {f} still exists on media server after deletion attempt\n")
                        alldeleted = False
                if alldeleted:
                    print(f"successfully deleted {film['disp_title']} from tvheadend\n")

    except Exception as e:
        errorExit(f"tvhtokodi enncountered an error: {e}")


if __name__ == "__main__":
    main()
