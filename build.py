"""Build the site into _site/ for GitHub Pages.

Copies the app files and writes clock.appcache, whose version line is a hash
of those files, so every change makes the phone download the new version.

    python build.py
"""
import hashlib
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, '_site')

# Files the phone keeps offline. Add new assets (icons, css, js) here.
CACHED_FILES = [
    'index.html',
    'apple-touch-icon.png',
    'fonts/DSEG7Classic-BoldItalic.woff',
    'fonts/DSEG14Classic-BoldItalic.woff',
]


def build_manifest():
    digest = hashlib.sha1()
    for name in CACHED_FILES:
        with open(os.path.join(ROOT, name), 'rb') as f:
            digest.update(f.read())
    lines = ['CACHE MANIFEST', '# version ' + digest.hexdigest()[:12]]
    lines += CACHED_FILES
    # Everything else (the wttr.in weather requests) goes to the network.
    lines += ['', 'NETWORK:', '*', '']
    return '\n'.join(lines).encode('utf-8')


def build():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    for name in CACHED_FILES:
        dest = os.path.join(OUT, name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, name), dest)
    with open(os.path.join(OUT, 'clock.appcache'), 'wb') as f:
        f.write(build_manifest())


if __name__ == '__main__':
    build()
    print('Built ' + OUT)
