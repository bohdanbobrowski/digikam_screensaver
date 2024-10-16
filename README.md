# DigiKam Screensaver

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/bohdanbobrowski/digikam_screensaver/graphs/commit-activity) [![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/) ![GitHub all releases](https://img.shields.io/github/downloads/bohdanbobrowski/digikam_screensaver/total) ![GitHub release (with filter)](https://img.shields.io/github/v/release/bohdanbobrowski/digikam_screensaver) ![GitHub Release Date - Published_At](https://img.shields.io/github/release-date/bohdanbobrowski/digikam_screensaver)

Windows screensaver, from pictures loaded out from DigiKam database in Python.

As for now - this is just for Windows.

## Features

- Takes random starred photos from digikam4.db SQLite databaser file and shows on your beloved window screen.
- Some configuration is needed.
- Database is opened in read-only mode!
- Pressing <F-12> will (obviously) turn off screen saver, and open given picture in associated app.

## What does not work

- preview is displayed in window instead of in dedicated screen.

## Dev environment

This will work on Windows cmd:

    git clone git@github.com:bohdanbobrowski/digikam_screensaver.git
    cd digikam_screensaver
    python -m venv venv
    venv\Scripts\activate
    pip install -e '.[dev]'

Run configuration windows first:

    python digikam_screensaver/screen_saver.py /c

It should look like this:

![digikam_screensaver_configuration_window.jpg](assets%2Fdigikam_screensaver_configuration_window.jpg)

Then, to test how does it work just type:

    python digikam_screensaver/screen_saver.py /s

Preview mode can be reached by typing:

    python digikam_screensaver/screen_saver.py /c

### Building own *.scr

If all required stuff is installed in system, this command should make the job:

    python digikam_digikam_screensaver_build.py

You'll find exe in `.\dist` folder - just rename it and install.

## Documentation and inspiration

1. https://github.com/SirGnip/arcade_screensaver_framework
2. https://github.com/gaming32/Windows-Screensaver
