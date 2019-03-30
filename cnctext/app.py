#!/usr/bin/env python

import sys
import os
import contextlib
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from io import StringIO, SEEK_SET

from .geometry import *
from .grbl import GrblCodeGenerator


LINE_SPREAD = 0.7
CHAR_HEIGHT = 2.6

TOTAL_WIDTH = 23.0

HELP_DESCRIPTION = """
Generates CNC program for engraving cable markers.
"""
HELP_EPILOG = """
Each text line may contain a gap, indicated by more than one space.
Text after the gap will be right aligned.

The generated code will produce two markers at G54 and G55 unless
the --no-pair argument is used.

Supported fonts are .chr files from http://ncplot.com/stickfont/stickfont.htm.
"""
HELP_LINE_ARGUMENT = """
One or two lines of input, or "-" to read from stdin (tab-separated).
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
    # Leave space for descenders on bottom-most line
    base_y = LINE_SPREAD

    sink = StringIO()

    gen = GrblCodeGenerator(sink, coord_sys=coord_sys)
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

    if (len(lines) > 2):
        raise ValueError(f"Too many lines ({len(lines)} > 2)")

    if (options.double and len(lines) > 1):
        raise ValueError(f"Too many lines for --double mode")

    f = Font.load("cnctext/fonts/default.chr")
    geom_lines = [Line(f, x) for x in lines]

    with smart_open(options.out, "wt") as o:
        print(make_g_code(geom_lines, "G54", options.double), file=o)
        if (options.pair):
            print(make_g_code(geom_lines, "G55", options.double), file=o)


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
        print(str(e))
        sys.exit(1)
    except ValueError as e:
        print(str(e))
        sys.exit(1)


if (__name__ == "__main__"):
    console_entry_point()