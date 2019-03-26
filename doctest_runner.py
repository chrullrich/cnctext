#!/usr/bin/env python

import doctest


if (__name__ == "__main__"):
    from cnctext import geometry
    doctest.testmod(geometry)
