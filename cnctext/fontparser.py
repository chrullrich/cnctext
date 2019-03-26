from arpeggio.cleanpeg import ParserPython, OneOrMore, Optional, ZeroOrMore, EOF, _
from arpeggio import PTNodeVisitor, visit_parse_tree


def comment():
    return _(r"#.*$")

def char_code():
    return _(r"[0-9A-F]{2}")

def number():
    return Optional("-"), _(r"\d+")

def point():
    return number, ",", number

def stroke():
    return ";", OneOrMore(point, eolterm=True)

def character():
    return "CHR_", char_code, number, OneOrMore(stroke, eolterm=True)

def font():
    return OneOrMore(character), EOF


class FontVisitor(PTNodeVisitor):
    def visit_char_code(self, node, children):
        return int(node.value, 16)

    def visit_number(self, node, children):
        if (len(children) == 1):
            return int(children[0], 10)
        else:
            return -int(children[1], 10)

    def visit_point(self, node, children):
        return tuple(children)

    def visit_stroke(self, node, children):
        return children

    def visit_character(self, node, children):
        return children[0], children[1], children[2:]

    def visit_font(self, node, children):
        return children


def parse(fontfile):
    parser = ParserPython(font, comment)
    with open(fontfile, "rt") as f:
        fontdata = f.read()
        tree = parser.parse(fontdata)

    return visit_parse_tree(tree, FontVisitor())


