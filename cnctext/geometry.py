#!/usr/bin/env python

import itertools
import re

from numpy import array
from .fontparser import parse


GAP_RE = re.compile(r"  +")


class Transformation:
    """
    Coordinate transformation matrix.

    With no arguments, it is initially an identity transformation:

    >>> t = Transformation()
    >>> t
    <Transformation: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]>

    It can be called to transform a point (x, y):

    >>> pt = (3, 4)
    >>> t(pt)
    (3.0, 4.0)

    Scaling and translation vectors can be set later:

    >>> Transformation().scale(2, 0.5)
    <Transformation: [[2.0, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 1.0]]>

    >>> Transformation().translate(3, 5)
    <Transformation: [[1.0, 0.0, 3.0], [0.0, 1.0, 5.0], [0.0, 0.0, 1.0]]>

    They can also be set using arguments during construction:

    >>> t = Transformation((2, 0.5), (3, 5))
    >>> t
    <Transformation: [[2.0, 0.0, 3.0], [0.0, 0.5, 5.0], [0.0, 0.0, 1.0]]>

    Transformation is done as a single step, i.e. translation
    is effectively applied after scaling:

    >>> t((3, 4))
    (9.0, 7.0)
    """
    def __init__(self, scale=None, translate=None):
        """
        :param scale: Scaling vector (x, y)
        :param translate: Translation vector (x, y)

        >>> Transformation((2, 3), (4, 5))
        <Transformation: [[2.0, 0.0, 4.0], [0.0, 3.0, 5.0], [0.0, 0.0, 1.0]]>
        """
        self.matrix = array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])

        # Assign directly; delegating to scale()/translate()
        # would scale the translation vector.
        if (scale):
            self.matrix[0][0] = scale[0]
            self.matrix[1][1] = scale[1]
        if (translate):
            self.matrix[0][2] = translate[0]
            self.matrix[1][2] = translate[1]

    def scale(self, x, y):
        """
        Scales the scaling vector.

        :param x: Scaling factor, x direction
        :param y:  Scaling factor, y direction
        :return: Modified transformation

        >>> Transformation().scale(2, 3)
        <Transformation: [[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 1.0]]>

        >>> Transformation().scale(2, 3).scale(2, 2)
        <Transformation: [[4.0, 0.0, 0.0], [0.0, 6.0, 0.0], [0.0, 0.0, 1.0]]>
        """
        self.matrix = self.matrix @ array([[x, 0, 0], [0, y, 0], [0, 0, 1]])
        return self

    def translate(self, x, y):
        """
        Modifies the translation vector.

        :param x: Translation offset, x direction
        :param y: Translation offset, y direction
        :return: Modified transformation

        >>> Transformation().translate(1, 2)
        <Transformation: [[1.0, 0.0, 1.0], [0.0, 1.0, 2.0], [0.0, 0.0, 1.0]]>

        >>> Transformation().translate(1, 2).translate(-3, -4)
        <Transformation: [[1.0, 0.0, -2.0], [0.0, 1.0, -2.0], [0.0, 0.0, 1.0]]>
        """
        self.matrix = self.matrix @ array([[1, 0, x], [0, 1, y], [0, 0, 1]])
        return self

    def __call__(self, pt):
        """
        Transforms a point (x, y).

        :param pt: The point to transform, as a sequence (x, y)
        :return: The transformed point, as a tuple (x, y)

        >>> t = Transformation((2, 3), (1, 2))
        >>> t((4,5))
        (9.0, 17.0)
        """
        return tuple((self.matrix @ (array([*pt, 1]))).tolist()[:2])

    def __str__(self):
        """
        >>> Transformation()
        <Transformation: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]>
        """
        return f"<Transformation: {self.matrix.tolist()}>"

    def __repr__(self):
        return str(self)


class Character:
    def __init__(self, cellwidth, strokes):
        self.cellwidth = cellwidth
        self.strokes = strokes

    def scaled(self, x, y):
        """
        Returns the cell width and strokes of the character,
        scaled by the given factors.

        >>> c = Character(20, [[(0, 0), (10, 10), (20, 0), (0, 0)]])
        >>> c.scaled(0.5, 0.5)
        (10.0, [[(0.0, 0.0), (5.0, 5.0), (10.0, 0.0), (0.0, 0.0)]])

        :param x: X component of scaling vector.
        :param y: Y component of scaling vector.
        :returns: tuple of (width, strokes)
        """
        scaledwidth = self.cellwidth * x

        xfrm = Transformation((x, y))
        scaledstrokes = [[xfrm(pt) for pt in s] for s in self.strokes]

        return scaledwidth, scaledstrokes


class Font:
    def __init__(self):
        self.characters = {}

        # Height above the baseline. We assume that descenders do not go down too far.
        self.height = 0

    def __getitem__(self, code):
        return self.characters[code]

    def __contains__(self, code):
        return code in self.characters

    @classmethod
    def load(cls, fontfile):
        """
        Loads a font from a file.

        >>> f = Font.load("cnctext/fonts/test.chr")
        >>> f[0x2b].cellwidth
        26
        >>> f[0x2b].strokes
        [[(13, 18), (13, 0)], [(4, 9), (22, 9)]]

        :param fontfile: Path to font definition
        :returns: Font.
        """
        inst = cls()
        chardata = parse(fontfile)
        for code, width, strokes in chardata:
            inst.characters[code] = Character(width, strokes)
            inst.height = max(inst.height, max(p[1] for s in strokes for p in s))

        # Add synthetic space if needed; two-thirds the width of the
        # narrowest character in the font.
        if (not 32 in inst.characters):
            minwidth = min([c.cellwidth for c in inst.characters.values()])
            inst.characters[32] = Character(minwidth * 2.0 / 3.0, [])

        # In the default font the slash has the same width as the digits.
        # This is ugly; resize it.
        if (inst.characters[47].cellwidth == inst.characters[48].cellwidth):
            inst.characters[47] = Character(*inst.characters[47].scaled(0.5, 1))

        # Similarly, shorten the hyphen.
        inst.characters[45] = Character(*inst.characters[45].scaled(0.75, 1))

        return inst


class GeometryError(Exception):
    def __str__(self):
        return f"GeometryError: {self.args[0]}: \"{self.args[1]}\""


class Line:
    MIN_GAP_WIDTH = 2.0     # Currently fixed gap width
    MAX_ASPECT_RATIO = 1.25
    MIN_ASPECT_RATIO = 0.75

    def __init__(self, font, text):
        """
        >>> f = Font.load("cnctext/fonts/test.chr")
        >>> l = Line(f, "+++  +++")
        >>> l.has_gap
        True
        >>> l.codes
        [[43, 43, 43], [43, 43, 43]]

        :param font: Font to be used for this line.
        :param text: Text of this line.
        """
        self.gap_width = Line.MIN_GAP_WIDTH
        self.font = font

        self.parts = re.split(GAP_RE, text)
        if (len(self.parts) > 2):
            raise ValueError("Line must not have more than one gap")

        self.codes = [list(p.encode("us-ascii")) for p in self.parts]
        self.chars = [[self.font[x] for x in p] for p in self.codes]

    def has_gap(self):
        return len(self.parts) == 2

    @property
    def all_characters(self):
        return itertools.chain(*self.chars)

    def width(self):
        return sum((c.cellwidth for c in self.all_characters))

    def scaling(self, size):
        """
        Returns the scale factors (x, y) to use for this line.

        :param size: Tuple (x, y) of available space in font size units.
        """
        x = size[0]
        if (self.has_gap()):
            x -= self.gap_width

        sx = x / self.width()
        sy = size[1] / self.font.height

        aspect = sx / sy

        if (aspect < Line.MIN_ASPECT_RATIO):
            raise GeometryError("Bad aspect ratio; font too narrow", "  ".join(self.parts))

        # If the font is getting stretched too much horizontally,
        # limit the stretching and, if there is one, widen the gap
        # so the result takes up the entire available width.
        if (aspect > Line.MAX_ASPECT_RATIO):
            sx = sy * Line.MAX_ASPECT_RATIO
            if (self.has_gap()):
                self.gap_width = size[0] - (self.width() * sx)

        return (sx, sy)

    def galley(self, sx, sy):
        result = []
        x = 0.0

        for p in self.chars:
            for c in p:
                cw, cs = c.scaled(sx, sy)
                result.append((x, cs))
                x += cw

            if (self.has_gap()):
                x += self.gap_width

        return result
