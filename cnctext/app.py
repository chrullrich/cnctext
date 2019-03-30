#!/usr/bin/env python

from io import StringIO

from .geometry import *
from .grbl import GrblCodeGenerator


LINE_SPREAD = 0.7
CHAR_HEIGHT = 2.6

TOTAL_WIDTH = 23.0


def offset(base, points):
    return [(round(pt[0] + base[0], 3), round(pt[1] + base[1], 3))
            for pt in points]


def make_g_code(lines, coord_sys):
    # Leave space for descenders on bottom-most line
    base_y = LINE_SPREAD

    sink = StringIO()

    gen = GrblCodeGenerator(sink, coord_sys=coord_sys)
    gen.start()

    # Lines are from top to bottom
    for line in reversed(lines):

        sx, sy = line.scaling((TOTAL_WIDTH, CHAR_HEIGHT))
        galley = line.galley(sx, sy)

        for base_x, strokes in galley:
            
            for stroke in strokes:

                gen.polyline(offset((base_x, base_y), stroke))

        base_y += (LINE_SPREAD + CHAR_HEIGHT)

    gen.stop()

    sink.seek(0, 0)
    return sink.read()


def main():
    f = Font.load("cnctext/fonts/default.chr")
    l1 = Line(f, "1/15  LAN")
    l2 = Line(f, "fw-primary")

    try:
        print(make_g_code([l1, l2], "G54"))
        print(make_g_code([l1, l2], "G55"))
    except GeometryError as e:
        print(str(e))


if (__name__ == "__main__"):
    main()
