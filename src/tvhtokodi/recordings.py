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
"""recordings module for tvhtokodi"""

import re
import sys
import time

import tvhtokodi
from tvhtokodi import errorNotify
from tvhtokodi.tvh import allRecordings


def cleanStringStart(xstr, remove="new:"):
    try:
        if xstr is None:
            return None
        xs = xstr[len(remove) :] if xstr.lower().startswith(remove) else xstr
        return xs.strip()
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def cleanTitle(title):
    """rules to clean up the title string."""
    try:
        xt = cleanStringStart(title, remove="new:")
        xt = cleanStringStart(xt, remove="live:")
        return xt
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def tidyRecording(rec):
    """retrieve the info we want about each recording."""
    try:
        oprec = {
            "channelname": rec.get("channelname"),
            "description": rec.get("disp_description", None),
            "duration": rec.get("duration"),
            "episode": rec.get("episode_disp", None),
            "extratext": rec.get("disp_extratext", None),
            "filename": rec.get("filename"),
            "filesize": rec.get("filesize"),
            "recorddate": rec.get("start"),
            "status": rec.get("status"),
            "subtitle": cleanStringStart(rec.get("disp_subtitle", ""), " - "),
            "summary": rec.get("disp_summary", None),
            "title": cleanTitle(rec.get("disp_title")),
            "uuid": rec.get("uuid"),
            "start_real": rec.get("start_real", 0),
            "stop_real": rec.get("stop_real", 0),
            "disp_description": rec.get("disp_description", None),
            "ctimestart": time.ctime(rec.get("start_real", None)),
        }
        extdesc = rec.get("disp_extratext", None)
        if extdesc:
            oprec["description"] += f". {extdesc}"
        oprec["season"], oprec["episode"] = getEpisode(rec.get("episode_disp", None))
        return oprec
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def getEpisode(eps):
    """extracts the season and episode numbers if they exist

    the input string, eps,  is of the form:
    ''
    'Episode 37'
    'Season 12.Episode 2'
    """
    try:
        episode = None
        season = None
        spatt = r"^Season (\d+).*$"
        epatt = r"^.*Episode (\d+).*$"
        if eps is not None:
            smatch = re.match(spatt, eps)
            if smatch:
                season = smatch.group(1)
            ematch = re.match(epatt, eps)
            if ematch:
                episode = ematch.group(1)
        return season, episode
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def recordedTitles():
    """Obtain all recorded titles as a dictionary of lists of those recordings."""
    try:
        recs, tot = allRecordings()
        titles = {}
        for rec in recs:
            show = tidyRecording(rec)
            if show["title"] not in titles:
                titles[show["title"]] = []
            # _ = titles.get(show["title"], [])
            titles[show["title"]].append(show)
        return recs, titles
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
