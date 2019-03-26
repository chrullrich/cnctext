#!/usr/bin/env python

import doctest


if (__name__ == "__main__"):
    from cnctext import app
    doctest.testmod(app)
