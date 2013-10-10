
from . import settings
import simplejson
import random

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
                self.seed = ( self.seed << 4 ) | ord(char)
            self.seed %= 100000

        self.seed_name = seed_string
        self.form = None
        random.seed(self.seed)

    def out(self):
        o = []
        for center in self.centers:
            #if center.border:
            #    continue
            o.append(unicode(center))
            o.append(u"text {0.point.x}:{0.point.y} {0.proximity:.0f}".format(center))
        for edge in list(self.edges):
            o.append(unicode(edge))
        return u'\n'.join(o)

    def out_polygons(self):
        verticles = []
        conn = []
        colors = []
        vcindex = 0
        max_pr = max(self.centers, key=lambda x: x.proximity).proximity
        min_pr = min(self.centers, key=lambda x: x.proximity).proximity

        def get_color_intens(target):
            #~ nprox = float(target.proximity - min_pr)
            #~ pr = ( nprox / float(max_pr - min_pr) ) if nprox else 0.0
            #~ return pr
            return float(target.region_type)

        def get_color(center, intens):
            if center.ocean:
                return [0.0, 0.0, 0.5, 1.0]
            if center.water:
                return [0.0, 0.0, 1.0, 1.0]
            return [0.0, intens, 0.0, 1.0]

        for p in self.centers:
            if p.border:
                continue
            for edge in p.borders:
                if not edge.v0 or not edge.v1:
                    continue
                verticles.extend([
                    [p.point.x, p.point.y, p.point.z],
                    [edge.v0.point.x, edge.v0.point.y, edge.v0.point.z],
                    [edge.v1.point.x, edge.v1.point.y, edge.v1.point.z]])
                conn.append([vcindex, vcindex + 1, vcindex + 2])
                colors.append([get_color(p, get_color_intens(tgt)) \
                        for tgt in (p, edge.v0, edge.v1)])
                vcindex += 3
        out = {
            "width": self.width,
            "height": self.height,
            "depth_min": self.height_min,
            "depth": self.height_max + 5.0,
            "verticles": verticles,
            "conn": conn,
            "colors": colors
        }
        return simplejson.dumps(out)
