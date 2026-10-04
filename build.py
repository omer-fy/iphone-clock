"""Build the site into _site/ for GitHub Pages.

Copies the app files, generates prayers.json (prayer times and Hijri dates
from AlAdhan), and writes clock.appcache, whose version line is a hash of all
of them, so every change makes the phone download the new version.

prayers.json is fetched here rather than by the phone because iOS 9 doesn't
trust the root certificate api.aladhan.com chains to (USERTrust RSA). Served
from GitHub Pages it uses the same certificate as the app itself, and it is
part of the offline cache.

    python build.py
"""
import datetime
import hashlib
import json
import os
import shutil
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, '_site')

# Files the phone keeps offline. Add new assets (icons, css, js) here.
CACHED_FILES = [
    'index.html',
    'apple-touch-icon.png',
    'fonts/inter-latin-300-normal.woff',
    'fonts/inter-latin-400-normal.woff',
    'fonts/inter-tight-latin-500-normal.woff',
]
PRAYERS_FILE = 'prayers.json'

PRAYER_LOCATION = {
    'latitude': 43.4516,    # Kitchener, Ontario
    'longitude': -80.4925,
    'method': 2,            # AlAdhan calculation method 2 = ISNA
}
PRAYERS = ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']


def fetch_year(year):
    url = ('https://api.aladhan.com/v1/calendar/%d?latitude=%s&longitude=%s&method=%s'
           % (year, PRAYER_LOCATION['latitude'], PRAYER_LOCATION['longitude'],
              PRAYER_LOCATION['method']))
    req = urllib.request.Request(url, headers={'User-Agent': 'iphone-clock build'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.load(resp)
    if body.get('code') != 200:
        raise RuntimeError('AlAdhan returned %r for %d' % (body.get('code'), year))
    return body['data']


def prayer_data():
    """This month through the end of next year, as compact JSON.

    {"2026-10": [{"t": ["06:05", ...6 times], "h": [23, 4, "1448"]}, ...], ...}
    Day N of the month is at index N - 1; "h" is the Hijri [day, month, year].
    Covering through next year keeps the clock working for at least a year
    even if the scheduled rebuild stops running.
    """
    today = datetime.date.today()
    months = {}
    for year in (today.year, today.year + 1):
        for month, days in fetch_year(year).items():
            month = int(month)
            if (year, month) < (today.year, today.month):
                continue
            entries = [None] * len(days)
            for d in days:
                hijri = d['date']['hijri']
                entries[int(d['date']['gregorian']['day']) - 1] = {
                    # "06:05 (EDT)" -> "06:05"
                    't': [d['timings'][name][:5] for name in PRAYERS],
                    'h': [int(hijri['day']), hijri['month']['number'], hijri['year']],
                }
            months['%d-%02d' % (year, month)] = entries
    return json.dumps(months, separators=(',', ':'), sort_keys=True).encode('utf-8')


def build_manifest(prayers):
    digest = hashlib.sha1()
    for name in CACHED_FILES:
        with open(os.path.join(ROOT, name), 'rb') as f:
            digest.update(f.read())
    digest.update(prayers)
    lines = ['CACHE MANIFEST', '# version ' + digest.hexdigest()[:12]]
    lines += CACHED_FILES + [PRAYERS_FILE]
    # Everything else (the wttr.in weather requests) goes to the network.
    lines += ['', 'NETWORK:', '*', '']
    return '\n'.join(lines).encode('utf-8')


def build():
    prayers = prayer_data()
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    for name in CACHED_FILES:
        dest = os.path.join(OUT, name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, name), dest)
    with open(os.path.join(OUT, PRAYERS_FILE), 'wb') as f:
        f.write(prayers)
    with open(os.path.join(OUT, 'clock.appcache'), 'wb') as f:
        f.write(build_manifest(prayers))


if __name__ == '__main__':
    build()
    print('Built ' + OUT)
