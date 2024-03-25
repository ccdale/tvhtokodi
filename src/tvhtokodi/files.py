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
import os
import sys

from fabric import Connection

import tvhtokodi
from tvhtokodi import errorNotify


def sendFileTo(fn):
    """transfers file 'fn' via ssh to the sshhost."""
    try:
        mhost = tvhtokodi.cfg["sshhost"]
        muser = tvhtokodi.cfg["sshuser"]
        mkeyfn = os.path.abspath(os.path.expanduser(f'~/.ssh/{tvhtokodi.cfg["keyfn"]}'))
        ckwargs = {"key_filename": mkeyfn}
        bfn = os.path.basename(fn)
        ofn = os.path.abspath(
            os.path.expanduser(f"{tvhtokodi.cfg['destination']}/{bfn}")
        )
        print(f"sending {fn} to druid as {ofn}")
        with Connection(host=mhost, user=muser, connect_kwargs=ckwargs) as c:
            c.put(fn, ofn)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def splitfn(path):
    try:
        """split a filename into a list of dir, base, ext"""
        parts = os.path.split(path)
        pbase, pext = os.path.splitext(parts[1])
        return [parts[0], pbase, pext]
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def findExtraFile(path, ext):
    """find a file with the same name as 'path' but with extension 'ext'"""
    try:
        pdir, pfile, pext = splitfn(path)
        for f in os.listdir(pdir):
            if f.startswith(pfile) and f.endswith(ext):
                return os.path.abspath(os.path.join(pdir, f))
        return None
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def makeFileList(path):
    """make a list of files corresponding to the recordings in tvheadend

    path is the path to the recording file

    will look for .txt, .nfo, and .srt files with the same name as the recording
    .txt files are assumed to be comskip files
    .nfo files are assumed to be kodi metadata files
    .srt files are assumed to be subtitles
    """
    try:
        flist = [path]
        extensions = [".txt", ".nfo", ".srt"]
        for ext in extensions:
            extra = findExtraFile(path, ext)
            if extra:
                flist.append(extra)
        return flist
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def dirFileList(path):
    try:
        if os.path.isdir(path):
            return [
                f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
            ]
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
