
from . import settings
import simplejson

class Map(object):

    def __init__(self, seed_string="new map"):
        self.centers = set()
        self.corners = set()
        self.edges = set()
        self.seed = 412496234
        self.height = settings.GENERATOR_SIZE_H
        self.width = settings.GENERATOR_SIZE_W

        if seed_string:
            for char in seed_string:
                self.seed = ( seed << 4 ) | ord(char)
            self.seed %= 100000

        self.seed_name = seed_string
        self.form = None

    def out(self):
        o = []
        for center in self.centers:
            o.append(unicode(center))
        for edge in list(self.edges):
            o.append(unicode(edge))
        return u'\n'.join(o)

    def out_polygons(self):
        verticles = []
        conn = []
        colors = []
        vcindex = 0
        for p in self.centers:
            color = 1 if p.ocean or p.water else 0
            for edge in p.borders:
                if not edge.v0 or not edge.v1:
                    continue
                verticles.extend([
                    [p.point.x, p.point.y, p.point.z],
                    [edge.v0.point.x, edge.v0.point.y, edge.v0.point.z],
                    [edge.v1.point.x, edge.v1.point.y, edge.v1.point.z]])
                conn.append([vcindex, vcindex + 1, vcindex + 2])
                colors.extend([color, color, color])
                vcindex += 3
        out = {
            "width": self.width,
            "height": self.height,
            "depth": 30,
            "verticles": verticles,
            "conn": conn,
            "colors": colors
        }
        return simplejson.dumps(out)
