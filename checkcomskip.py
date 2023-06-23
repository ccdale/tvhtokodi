import json
import os
import sys

from tvhtokodi import errorNotify, readConfig
from tvhtokodi.files import sendFileTo
from tvhtokodi.tvh import allRecordings


def advertRecordings():
    try:
        recs, total = allRecordings()
        return [r for r in recs if not r["channelname"].startswith("BBC")]
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def advertFileNames():
    try:
        recs = advertRecordings()
        return [f["filename"] for f in recs]
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def doComSkipFiles(afn):
    try:
        fns = []
        for fn in afn:
            f, ext = os.path.splitext(fn)
            txt = f"{f}.txt"
            if not os.path.exists(txt):
                fns.append(fn)
        return fns
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


if __name__ == "__main__":
    # cfg = readConfig()
    # afn = advertFileNames()
    with open("advertfiles", "r") as ifn:
        afn = json.load(ifn)
    csafn = doComSkipFiles(afn)
    with open("docomskip.json", "w") as ofn:
        json.dump(csafn, ofn, indent=4)
