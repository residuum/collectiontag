**Due to Github's determination to be the "world’s leading AI-powered developer platform" I will move my projects to [Codeberg](https://codeberg.org/Residuum)**

Python script for tagging your music collection with genres and keywords from [discogs](https://www.discogs.com/) and [Bandcamp](https://bandcamp.com/)

# Pre-requisites
Python 3 with the following packages:

- pytaglib
- python3-discogs-client
- pyquery
- lxml
- urllib3

Install via

    pip3 install pytablib python3-discogs-client pyquery lxml urllib3

# Configuration
- `GENRE_SEPARATOR`: separator string between different tags. Genres from discogs contain `,` and 
may contain whitespace, so these characters should not be used.
- `DISCOGS_TOKEN`: Getting data from discogs requires a token, which in turn requires a discogs account. 
Using [discogs developer settings](https://www.discogs.com/settings/developers) you can generate a new token.
- `MUSIC_FOLDER`: Path to your music folder

# Running the script
    python3 collectiontag.py

# Assumptions in the Script
- Artist, album names and album artists are correctly tagged.
- Compilations with multiple artists have album artists set to `Various` or `Various Artists`
- Downloads from Bandcamp still contain the original comment: `Visit https://<profile>.bandcamp.com`

# License
Copyright 2023 Thomas Mayer <thomas@residuum.org>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


