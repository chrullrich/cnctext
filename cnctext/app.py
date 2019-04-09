#!/usr/bin/env python

import sys
import os
import itertools
import contextlib
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from io import StringIO, SEEK_SET

from .geometry import *
from .grbl import GrblCodeGenerator


LINE_SPREAD = 0.8
CHAR_HEIGHT = 2.5

TOTAL_WIDTH = 23.0

HELP_DESCRIPTION = """
Generates CNC program for engraving cable markers.
"""
HELP_EPILOG = """
Each text line may contain a gap, indicated by more than one space.
Text after the gap will be right aligned.

Depending on the number of input lines, code for either one or two marker
variants will be produced:

|        |    | Line 1 |         |        |    | Line 3 |
| Line 1 | or | Line 2 |   and   | Line 3 | or | Line 4 |

This means that, to make two single-line markers, the first line must be empty.

The generated code will place paired markers at G54/G55 and G56/G57.
If the --no-pair argument is used, single markers will be at G54 and G55.

Supported fonts are .chr files from http://ncplot.com/stickfont/stickfont.htm.

Built-in dimensions are for HellermannTyton cable markers IT18R (111-81821).
"""
HELP_LINE_ARGUMENT = """
One to four lines of text, or "-" to read from stdin (tab-separated).
"""


@contextlib.contextmanager
def smart_open(filename=None, mode="r"):
    if filename and filename != '-':
        fh = open(filename, mode)
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()


def offset(base, points):
    return [(round(pt[0] + base[0], 3), round(pt[1] + base[1], 3))
            for pt in points]


def make_g_code(lines, coord_sys, double_height):

    # We don't support G59.[123] for now.
    if (type(coord_sys) != int or coord_sys < 54 or coord_sys > 59):
        raise ValueError(f"Not a valid coordinate system: {coord_sys}")

    # Leave space for descenders on bottom-most line
    base_y = LINE_SPREAD

    sink = StringIO()

    gen = GrblCodeGenerator(sink, coord_sys=coord_sys, z_move=6.0)
    gen.start()

    # Lines are from top to bottom
    for line in reversed(lines):

        line_height = CHAR_HEIGHT
        if (double_height):
            line_height += CHAR_HEIGHT + LINE_SPREAD

        sx, sy = line.scaling((TOTAL_WIDTH, line_height), double_height)
        galley = line.galley(sx, sy)

        for base_x, strokes in galley:

            for stroke in strokes:

                gen.polyline(offset((base_x, base_y), stroke))

        base_y += (LINE_SPREAD + CHAR_HEIGHT)

    gen.stop()

    sink.seek(0, SEEK_SET)
    return sink.read()


def main(options):
    if (options.LINE[0] == "-"):
        lines = sys.stdin.readline().strip().split("\t")
    else:
        lines = options.LINE

    # TODO: Make better.
    # Rearrange [1,2,3,4] to [[1,2],[3,4]].
    # Rearrange [1,2,3] to [[1,2],[3]].
    # Rearrange [1,2] to [[1,2]].
    if (len(lines) == 1):
        labels = [[lines[0]]]
    elif (len(lines) == 2):
        labels = [[lines[0], lines[1]]]
    elif (len(lines) == 3):
        labels = [[lines[0], lines[1]], [lines[2]]]
    elif (len(lines) == 4):
        labels = [[lines[0], lines[1]], [lines[2], lines[3]]]
    else:
        raise ValueError(f"Too many lines ({len(lines)} > 4)")

    if (options.double and len(lines) > 1):
        raise ValueError(f"Too many lines for --double mode")

    f = Font.load("cnctext/fonts/default.chr")
    geom_labels = [[Line(f, x) for x in lines] for lines in labels]

    # This works for up to three pairs. The fourth pair must use
    # G59.1 and G59.2, so we will need a different solution then.
    coord_sys = itertools.count(start=54)

    with smart_open(options.out, "wt") as o:
        for label in geom_labels:
            print(make_g_code(label, next(coord_sys), options.double), file=o)
            if (options.pair):
                print(make_g_code(label, next(coord_sys), options.double), file=o)


def console_entry_point():
    p = ArgumentParser(description=HELP_DESCRIPTION, epilog=HELP_EPILOG,
                       formatter_class=RawDescriptionHelpFormatter)
    p.add_argument("--double", action="store_true", help="Write single line at double height")
    p.add_argument("--no-pair", action="store_false", dest="pair",
                   help="Write single output at G54 only")
    p.add_argument("--out", "-o", help="Output file name", default="-")
    p.add_argument("--font", "-f", help="Font (.chr file) to use",
                   default=os.path.join(os.path.dirname(__file__), "fonts", "default.chr"))
    p.add_argument("LINE", nargs="+", help=HELP_LINE_ARGUMENT)

    try:
        main(p.parse_args())
        sys.exit(0)
    except GeometryError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if (__name__ == "__main__"):
    console_entry_point()
