#!/usr/bin/env python

from .geometry import *


LINE_SPREAD = 0.5
CHAR_HEIGHT = 2.8

TOTAL_WIDTH = 22.5

RAPID_FEED = 100
INTERPOLATE_FEED = 50
SPINDLE_SPEED = 500


PROLOG = f"""
G0 G54 X0 Y0 Z0.3 F{RAPID_FEED}
M3 S{SPINDLE_SPEED}
"""

EPILOG = """
M5
"""

def shift_point(pt, offset):
    return round(pt[0] + offset[0], 3), round(pt[1] + offset[1], 3)


def make_g_code(lines):
    yield from PROLOG.strip().splitlines()

    # Leave space for descenders on bottom-most line
    base_y = LINE_SPREAD

    # Lines are from top to bottom
    for line in reversed(lines):

        sx, sy = line.scaling((TOTAL_WIDTH, CHAR_HEIGHT))
        galley = line.galley(sx, sy)

        for base_x, strokes in galley:
            
            for stroke in strokes:

                # SP has empty stroke list
                if (not stroke):
                    continue

                # Rapid to the first point, lower tool.
                x, y = shift_point(stroke[0], (base_x, base_y))

                yield f"G0 X{x} Y{y} F{RAPID_FEED}"
                yield f"G1 Z-0.3 F{INTERPOLATE_FEED}"

                # Do remaining points.
                for point in stroke[1:]:

                    x, y = shift_point(point, (base_x, base_y))
                    yield f"G1 X{x} Y{y}"

                yield f"G0 Z0.3 F{RAPID_FEED}"

        base_y += (LINE_SPREAD + CHAR_HEIGHT)

    yield from EPILOG.strip().splitlines()


def main():
    f = Font.load("cnctext/fonts/default.chr")
    l1 = Line(f, "Christian")
    l2 = Line(f, "Lorem Ipsum")
    g = make_g_code([l2, l1])

    print("\n".join(g))


if (__name__ == "__main__"):
    main()

