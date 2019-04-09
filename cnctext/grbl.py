class GrblCodeGenerator:
    def __init__(self, out, **kwargs):
        self.out = out

        self.coord_sys = kwargs.get("coord_sys", 54)
        self.z_move = kwargs.get("z_move", 5.0)
        self.z_clear = kwargs.get("z_clear", 0.25)
        self.z_engrave = kwargs.get("z_engrave", -0.075)
        self.f_rapid = kwargs.get("f_rapid", 100)
        self.f_interpolate = kwargs.get("f_interpolate", 50)
        self.s_engrave = kwargs.get("s_engrave", 500)

        self.is_clear = True
        self.feed = -1

        self.last_pt = None

    def o(self, line):
        print(line, file=self.out)

    def f(self, feed):
        if (feed != self.feed):
            self.feed = feed
            return f" F{feed}"
        return ""

    def away(self):
        self.o(f"G0 Z{self.z_move}" + self.f(self.f_rapid))
        self.is_clear = True

    def up(self):
        if (not self.is_clear):
            self.o(f"G0 Z{self.z_clear}" + self.f(self.f_rapid))
            self.is_clear = True

    def down(self):
        if (self.is_clear):
            self.o(f"G1 Z{self.z_engrave}" + self.f(self.f_interpolate))
            self.is_clear = False

    def rapid(self, pt):
        self.up()
        self.o(f"G0 X{pt[0]} Y{pt[1]}")

    def engrave(self, pt):
        if (self.is_clear):
            self.down()
        self.o(f"G1 X{pt[0]} Y{pt[1]}" + self.f(self.f_interpolate))

    def start(self):
        self.o(f"G0 G{self.coord_sys}")
        self.away()
        self.o(f"G0 X0 Y0" + self.f(self.f_rapid))
        self.o(f"M3 S{self.s_engrave}")

    def stop(self):
        self.away()
        self.o(f"M5")

    def polyline(self, points):
        if (points):
            if (not self.last_pt or self.last_pt != points[0]):
                self.rapid(points[0])
            for pt in points[1:]:
                self.engrave(pt)