# DigiKam Screensaver
Windows screensaver, from pictures loaded out from DigiKam database in Python

## Plan for implementation

### 1. "Redneck" version

To start with, I prepared a simple script that only copies the specified number of starred images from the digiKam database (sqlite only). Such a prepared set can be displayed in one of the ready-made screen savers for Windows.

Usage (after installing this package in [*virtual*] environment):

    digikam_screensaver_copy_pictures

### 2. Real screensaver

And this is what I plan to implement:

- a fairly simple slide show, using one of the Python libraries
- possible simple configuration
- building the exe file with pyinstaller

**Additional goal:** to answer the question whether this is even possible using Python? Will such a slideshow be efficient, and is it possible to add some simple animation to the displayed photos?

## Documentation and inspiration

1. https://github.com/SirGnip/arcade_screensaver_framework