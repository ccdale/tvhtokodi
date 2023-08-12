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


# function to split a filename into a list of path components
def splitfn(path):
    try:
        """split a filename into a list of path components"""
        parts = os.path.split(path)
        pdir = parts[0]
        pfile = parts[1]
        pext = os.path.splitext(pfile)[1]
        return [pdir, pfile, pext]
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
