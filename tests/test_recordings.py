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
"""test module for the tvhtokodi.recordings module."""

from tvhtokodi.recordings import getEpisode


def test_getEpisode_emptystring():
    eps = ""
    season, episode = getEpisode(eps)
    assert season is None
    assert episode is None


def test_getEpisode_None():
    eps = None
    season, episode = getEpisode(eps)
    assert season is None
    assert episode is None


def test_getEpisode_both():
    eps = "Season 6.Episode 3"
    season, episode = getEpisode(eps)
    assert season == "6"
    assert episode is "3"


def test_getEpisode_large():
    eps = "Season 36.Episode 1223"
    season, episode = getEpisode(eps)
    assert season == "36"
    assert episode == "1223"


def test_getEpisode_episode_only():
    eps = "Episode 12"
    season, episode = getEpisode(eps)
    assert season is None
    assert episode == "12"
