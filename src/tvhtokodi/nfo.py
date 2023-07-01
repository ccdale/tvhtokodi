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
"""
nfo module for tvh application
"""

import sys
import time

from tvhtokodi import errorRaise


def makeNfoString(nfodict, maintag="episodedetails"):
    try:
        content = ""
        xmlargs = {"attrs": None, "oneline": True, "newline": True}
        for tag in nfodict:
            content += makeXmlTag(tag, nfodict[tag], **xmlargs)
        xmlargs["oneline"] = False
        return makeXmlTag(maintag, content, **xmlargs)
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def makeFilmNfo(show):
    try:
        mtags = nfoTags(show)
        mtags["premiered"] = show["year"]
        mtags["year"] = show["year"]
        return makeNfoString(mtags, "movie")
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def makeProgNfo(show):
    try:
        ptags = nfoTags(show)
        if (
            "subtitle" in show
            and show["subtitle"] is not None
            and len(show["subtitle"]) > 0
        ):
            ptags["showtitle"] = show["subtitle"]
        if "series" in show and show["series"] is not None:
            ptags["series"] = show["series"]
        return makeNfoString(ptags)
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def nfoTags(show):
    try:
        return {
            "title": show["title"],
            "plot": show["disp_description"],
            "startsecs": str(show["start_real"]),
            "stopsecs": str(show["stop_real"]),
            "start": time.ctime(show["start_real"]),
            "stop": time.ctime(show["stop_real"]),
            "durationsecs": str(show["duration"]),
            "duration": hmsDisplay(show["duration"]),
            "channel": show["channelname"],
        }
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def makeXmlAtts(attrs):
    try:
        satts = ""
        for attr in attrs:
            satts += attr + "=" + attrs[attr]
        return satts
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def makeXmlTag(tag, content, attrs=None, oneline=False, newline=True):
    try:
        filler = "\n" if oneline else ""
        xml = f"<{tag}"
        if content is None and attrs is not None:
            xml += makeXmlAtts(attrs)
            xml += " />"
        elif content is not None:
            if attrs is not None:
                xml += makeXmlAtts(attrs)
            xml += f">{filler}"
            xml += content + filler
            xml += f"</{tag}>"
        if newline and oneline:
            xml += "\n"
        return xml
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def valMod(value, divisor):
    try:
        return [int(value / divisor), value % divisor]
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def hms(seconds):
    try:
        hrs, rem = valMod(seconds, 3600)
        mins, secs = valMod(rem, 60)
        return [hrs, mins, secs]
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def displayWord(value, word):
    try:
        if value <= 0:
            return ""
        return f"{value} {word}" if value == 1 else f"{value} {word}s"
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def hmsDisplay(seconds):
    ret = ""
    try:
        h, m, s = hms(seconds)
        hstr = displayWord(h, "hour")
        mstr = displayWord(m, "minute")
        sstr = displayWord(s, "second")
        ret = ""
        if len(hstr) and len(mstr) and len(sstr):
            ret = f"{hstr}, {mstr} and {sstr}"
        elif len(hstr) and len(mstr):
            ret = f"{hstr} and {mstr}"
        elif len(hstr) and len(sstr):
            ret = f"{hstr}, 0 minutes and {sstr}"
        elif len(hstr):
            ret = hstr
        elif len(mstr) and len(sstr):
            ret = f"{mstr} and {sstr}"
        elif len(mstr):
            ret = mstr
        else:
            ret = sstr
        return ret
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)
