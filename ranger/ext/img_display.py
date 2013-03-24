# This software is distributed under the terms of the GNU GPL version 3.

"""Interface for w3mimgdisplay to draw images into the console

This module provides functions to draw images in the terminal using
w3mimgdisplay, an utilitary program from w3m (a text-based web browser).
w3mimgdisplay can display images either in virtual tty (using linux
framebuffer) or in a Xorg session.

w3m need to be installed for this to work.
"""

import termios, fcntl, struct, sys, os
from subprocess import Popen, PIPE

W3MIMGDISPLAY_PATH = '/usr/lib/w3m/w3mimgdisplay'
W3MIMGDISPLAY_OPTIONS = []

class ImgDisplayUnsupportedException(Exception):
    pass

def _get_font_dimensions():
    # Get the height and width of a character displayed in the terminal in
    # pixels.
    s = struct.pack("HHHH", 0, 0, 0, 0)
    fd_stdout = sys.stdout.fileno()
    x = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, s)
    rows, cols, xpixels, ypixels = struct.unpack("HHHH", x)

    return (xpixels // cols), (ypixels // rows)


def _w3mimgdisplay(commands):
    """Invoke w3mimgdisplay and send commands on its standard input."""
    path = os.environ.get("W3MIMGDISPLAY_PATH", None)
    if not path:
        path = W3MIMGDISPLAY_PATH
    process = Popen([path] + W3MIMGDISPLAY_OPTIONS, stdin=PIPE,
            stdout=PIPE, universal_newlines=True)

    # wait for the external program to finish
    output, _ = process.communicate(input=commands)

    return output

def generate_w3m_input(path, start_x, start_y, max_width, max_height):
    """Prepare the input string for w3mimgpreview

    start_x, start_y, max_height and max_width specify the drawing area.
    They are expressed in number of characters.
    """
    fontw, fonth = _get_font_dimensions()
    if fontw == 0 or fonth == 0:
        raise ImgDisplayUnsupportedException()

    max_width_pixels = max_width * fontw
    max_height_pixels = max_height * fonth

    # get image size
    cmd = "5;{}".format(path)
    output = _w3mimgdisplay(cmd).split()

    if len(output) != 2:
        raise Exception('Failed to execute w3mimgdisplay')

    width = int(output[0])
    height = int(output[1])

    # get the maximum image size preserving ratio
    if width > max_width_pixels:
        height = (height * max_width_pixels) // width
        width = max_width_pixels
    if height > max_height_pixels:
        width = (width * max_height_pixels) // height
        height = max_height_pixels

    return "0;1;{x};{y};{w};{h};;;;;{filename}\n4;\n3;".format(
            x = start_x * fontw,
            y = start_y * fonth,
            w = width,
            h = height,
            filename = path)

def draw(path, start_x, start_y, max_width, max_height):
    """Draw an image file in the terminal.

    start_x, start_y, max_height and max_width specify the drawing area.
    They are expressed in number of characters.
    """
    _w3mimgdisplay(generate_w3m_input(path, start_x, start_y, max_width, max_height))

def clear(start_x, start_y, width, height):
    """Clear a part of terminal display."""
    fontw, fonth = _get_font_dimensions()

    cmd = "6;{x};{y};{w};{h}\n4;\n3;".format(
            x = start_x * fontw,
            y = start_y * fonth,
            w = (width + 1) * fontw,
            h = height * fonth)

    _w3mimgdisplay(cmd)
