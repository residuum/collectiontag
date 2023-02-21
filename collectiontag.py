#!/usr/bin/env python

'''
LICENSE:
Copyright 2023 Thomas Mayer <thomas@residuum.org>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
#########################
# Configuration
# Characters like "," or "/" are used in discogs genres and styles, 
# whitespace may be part of tags.
GENRE_SEPARATOR = "; " 
# Get your Token from https://www.discogs.com/settings/developers
# click "Generate new token"
DISCOGS_TOKEN = "your_token"
# Full path to folder
MUSIC_FOLDER = "/path/to/your/music/folder"

# End configuration
#########################

import os
import datetime
import taglib
import discogs_client
from pyquery import PyQuery as pq
from lxml import etree
import urllib
import json
from collections import OrderedDict

# Tag names
GENRE_TAG = "GENRE"
ARTIST_TAG = "ARTIST"
ALBUM_TAG = "ALBUM"
ALBUMARTIST_TAG = "ALBUMARTIST"
DATE_TAG = "DATE"

# For Bandcamp only
COMMENT_TAG = "COMMENT"
DESCRIPTION_TAG = "DESCRIPTION"
TITLE_TAG = "TITLE"

# cache found discogs information
found_discogs = dict()
discogs = discogs_client.Client("Tagging script", user_token=DISCOGS_TOKEN)

# cache bandcamp info
found_bandcamp = dict()

class BandcampInfo:
    def __init__(self, href, keywords):
        self.href = href
        self.keywords = keywords

def has_empty_tag(tags, tagname):
    return not tagname in tags or not tags[tagname] or not tags[tagname][0]

def get_info_from_discogs(artist, album):
    results = discogs.search(album, artist=artist, type="release")
    # maybe add different formats for compilations
    if artist == "Various" or artist == "Various Artists":
        results = discogs.search(album, type="release")
    else:
        results = discogs.search(album, artist=artist, type="release")
    matches = results.page(1)
    if len(matches) == 0:
        print("Not found:", artist, "-", album)
        return None
    if len(matches) == 1:
        return discogs.release(matches[0].id)
    # find the first release version with genres and styles from discogs
    for match in matches:
        release_data = discogs.release(match.id)
        if release_data.genres and release_data.styles:
            return release_data
    return discogs.release(matches[0].id)

def get_discogs_genres(track):
    # Tag genre only, if artist and album are tagged, otherwise no reliable data 
    # will be reliably and automatically found with this simple method.
    if (has_empty_tag(track.tags, ARTIST_TAG) or has_empty_tag(track.tags, ALBUM_TAG)):
        return list()
    artist = track.tags[ARTIST_TAG][0]
    album = track.tags[ALBUM_TAG][0]
    if not has_empty_tag(track.tags, ALBUMARTIST_TAG):
        artist = track.tags[ALBUMARTIST_TAG][0]
    if not artist in found_discogs:
        found_discogs[artist] = dict()
    if not album in found_discogs[artist]:
        print("Getting from discogs:", artist, "-", album)
        found_discogs[artist][album] = get_info_from_discogs(artist, album)
    release_data = found_discogs[artist][album]
    if not release_data:
        return list()
    genre_tags = list()
    if release_data.genres:
        genre_tags = genre_tags + release_data.genres
    if release_data.styles:
        genre_tags = genre_tags + release_data.styles
    return genre_tags

def tag_discogs_date(track):
    # Tag date only, if artist and album are tagged, otherwise no reliable data 
    # will be reliably and automatically found with this simple method.
    if (has_empty_tag(track.tags, ARTIST_TAG) or has_empty_tag(track.tags, ALBUM_TAG)):
        return
    artist = track.tags[ARTIST_TAG][0]
    album = track.tags[ALBUM_TAG][0]
    # we already downloaded the information for genres, if available
    if not artist in found_discogs:
        return
    if not album in found_discogs[artist]:
        return
    release_data = found_discogs[artist][album]
    if not release_data:
        return
    if release_data.year:
        track.tags[DATE_TAG] = list()
        track.tags[DATE_TAG].append(str(release_data.year))
        track.save()

def download_bandcamp_keywords(bandcamp_url, item_to_find):
    if not item_to_find:
        return list()

    overview_url = bandcamp_url + "/music"
    if not bandcamp_url in found_bandcamp:
        found_bandcamp[bandcamp_url] = dict()
        overview_dom = pq(url=overview_url)
        # ol#music-grid li a p.title
        # href of a points to release
        # p.title is item_to_find + optionally <br> and band
        listing = overview_dom("ol#music-grid li a")
        found_bandcamp[bandcamp_url] = dict()
        for l in listing:
            list_el = pq(l)
            title = list_el("p").contents()[0]
            href = list_el.attr("href")
            found_bandcamp[bandcamp_url][title.strip().lower()] = BandcampInfo(href, None)

    # only one release available, then overview redirects to release
    if len(found_bandcamp[bandcamp_url]) == 0:
        title = overview_dom("h2.trackTitle").contents()[0]
        json_data = json.loads(overview_dom('script[type="application/ld+json"]').html())
        keywords = list()
        if not "keywords" in json_data:
            keywords = json_data["keywords"] = list()
        print("Getting from bandcamp:", bandcamp_url, "-", item_to_find)
        keywords = json_data["keywords"]
        found_bandcamp[bandcamp_url][title.strip().lower()] = BandcampInfo(overview_url, keywords)

    if not item_to_find in found_bandcamp[bandcamp_url]:
        print("Not Found:", bandcamp_url, "-", item_to_find)
        return list()

    if not found_bandcamp[bandcamp_url][item_to_find].keywords:
        print("Getting from bandcamp:", bandcamp_url, "-", item_to_find)
        if not  found_bandcamp[bandcamp_url][item_to_find].href.startswith("http"):
            album_url = bandcamp_url + found_bandcamp[bandcamp_url][item_to_find].href 
        else:
            album_url = found_bandcamp[bandcamp_url][item_to_find].href 
        album_dom = pq(url=album_url)
        # Tags: 
        # <script type="application/ld+json"> JSON with property "keywords" and string array
        # </script>
        json_data = json.loads(album_dom('script[type="application/ld+json"]').html())
        if not "keywords" in json_data:
            found_bandcamp[bandcamp_url][item_to_find].keywords = json_data["keywords"] = list()
        found_bandcamp[bandcamp_url][item_to_find].keywords = json_data["keywords"]
    return found_bandcamp[bandcamp_url][item_to_find].keywords

def get_bandcamp_keywords(track):
    # Bandcamp keywords, format in comment or description:
    # Visit https://<profile>.bandcamp.com
    try:
        bandcamp_url = None
        if (not has_empty_tag(track.tags, COMMENT_TAG)
            and track.tags[COMMENT_TAG][0].startswith("Visit")
            and track.tags[COMMENT_TAG][0].endswith(".bandcamp.com")):
            bandcamp_url = track.tags[COMMENT_TAG][0].split(" ")[1]
        if (not has_empty_tag(track.tags, DESCRIPTION_TAG)
            and track.tags[DESCRIPTION_TAG][0].startswith("Visit")
            and track.tags[DESCRIPTION_TAG][0].endswith(".bandcamp.com")):
            bandcamp_url = track.tags[DESCRIPTION_TAG][0].split(" ")[1]
        if not bandcamp_url:
            return list()
        # Album or track
        item_to_find = None
        if not has_empty_tag(track.tags, ALBUM_TAG):
            item_to_find = track.tags[ALBUM_TAG][0]
        elif not has_empty_tag(track.tags, TITLE_TAG):
            item_to_find = track.tags[TITLE_TAG][0]
        if not item_to_find:
            return list()
        return download_bandcamp_keywords(bandcamp_url, item_to_find.lower())
    except:
        return list()

def analyse_and_tag(file):
    track = taglib.File(file)
    genre_tags = list()
    # if genres are already tagged, e.g. with Musicbrainz Picard, then use those
    if not has_empty_tag(track.tags, GENRE_TAG):
        genre_tags = track.tags[GENRE_TAG][0].split(GENRE_SEPARATOR)
        if "Playlist" in genre_tags:
            return
        if len(genre_tags) > 0 and len(genre_tags[0]) > 23:
            del genre_tags[0]
    new_tags = get_discogs_genres(track) + get_bandcamp_keywords(track)
    # only write, if tags are found, otherwise just use the current tags
    if len(new_tags) > 0:
        genre_tags = genre_tags + new_tags
        # filter for uniqueness
        genre_tags = list(OrderedDict.fromkeys(genre_tags))
        track.tags[GENRE_TAG] = list()
        track.tags[GENRE_TAG].append(GENRE_SEPARATOR.join(genre_tags))
        track.save()
    # Tag year if currently not set
    year = 0
    if not has_empty_tag(track.tags, DATE_TAG):
        try:
            date_as_string = track.tags[DATE_TAG][0]
            # parse yyyy-MM-dd as this may come from Musicbrainz
            if "-" in date_as_string:
                year = datetime.datetime.strptime(date_as_string, "%Y-%m-%d").year
            else:
                year = int(date_as_string)
        except:
            year = 0
    if (year < 1930 or year > 2023):
        tag_discogs_date(track)

for current_dir, _, files in os.walk(MUSIC_FOLDER):
    for filename in files:
        if filename.endswith(".mp3") or filename.endswith(".flac") or filename.endswith(".ogg"):
            relative_path = os.path.join(current_dir, filename)
            absolute_path = os.path.abspath(relative_path)
            analyse_and_tag(absolute_path)
