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

import sys

import tvhtokodi
from tvhtokodi import errorNotify
from tvhtokodi.tvh import allRecordings


def cleanStringStart(xstr, remove="new:"):
    try:
        if xstr is None:
            return None
        xs = xstr[len(remove) :] if xstr.lower().startswith(remove) else xstr
        return xs
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def cleanTitle(title):
    """rules to clean up the title string."""
    try:
        xt = cleanStringStart(title)
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
            "subtitle": cleanStringStart(rec.get("disp_subtitle", None), " - "),
            "summary": rec.get("disp_summary", None),
            "title": cleanTitle(rec.get("disp_title")),
            "uuid": rec.get("uuid"),
        }
        return oprec
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def recordedTitles():
    """Obtain all recorded titles as a dictionary of lists of those recordings."""
    try:
        recs, tot = allRecordings()
        titles = {}
        for rec in recs:
            show = tidyRecording(rec)
            _ = titles.get(show["title"], [])
            titles["title"].append(show)
        return recs, titles
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
