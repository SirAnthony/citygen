

from .module import Module
from .. import settings
from ..geom import Point, LightCenter
#from multiprocessing import Pool
from math import sin, cos, radians

class RoadSegment(object):
    def __init__(self, start_point, query, prev=None, reverse=False):
        self.reverse = reverse
        self.p1 = self.p2 = None
        self.next = self.prev = None
        if reverse:
            self.p2 = start_point
            self.next = prev
        else:
            self.p1 = start_point
            self.prev = prev
        self.query = query
        self.delay = 0
        self.fail = False
        self.done = False

    def get_prev(self):
        return self.next if self.reverse else self.prev

    def generate_next(self, pt_global, pt_local):
        if self.done:
            return

        reverse = self.reverse
        pst = self.p1 if not reverse else self.p2

        if not pt_global.check_point(pst.x, pst.y):
            self.fail = True
        if self.fail:
            return

        prev_pt = self.get_prev()
        if prev_pt:
            prev_pt = prev_pt.p1 if not reverse else prev_pt.p2
        p2 = pt_global.next_point(pst, prev_pt)
        p2 = pt_local.ajust_point(p2)
        if not p2:
            self.fail = True
            return

        if reverse:
            self.p1 = p2
        else:
            self.p2 = p2

        next_rd = RoadSegment(p2, self.query, self, reverse)
        self.query.append(next_rd)

        if reverse:
            self.prev = next_rd
        else:
            self.next = next_rd

        if not self.prev:
            self.prev = RoadSegment(pst, self.query, self, True)
            self.query.append(self.prev)

        self.done = True


    def __str__(self):
        return u"Road {0.p1} {0.p2}".format(self)


class GlobalGoals(object):

    def __init__(self, hmap, hlim, pmap):
        self.heights = hmap
        self.population = pmap
        (self.hmax, self.hmin) = hlim

    def check_point(self, x, y, mwidth=settings.GENERATOR_SIZE_W,
                                 mheight=settings.GENERATOR_SIZE_H,
                                 water=settings.GENERATOR_WATER):
        if 0 < x < mwidth and 0 < y < mheight:
            hwater = (water - 0.01) * (self.hmax - self.hmin) + self.hmin
            if self.heights[x][y] > hwater:
                return True
        return False

    def next_point(self, start, prev, sin=sin, cos=cos,
                        segment_angle=settings.MAINROAD_SEGMENT_ANGLE,
                        length=settings.MAINROAD_SEGMENT_LENGTH):
        min_angle, max_angle = 0, 360
        if prev:
            base_angle = prev.angle(start)
            min_angle = base_angle - segment_angle
            max_angle = base_angle + segment_angle
        angle = min_angle
        pmap = self.population
        hmap = self.heights
        old_pop = 0
        new_point = None
        ox, oy = start.x, start.y
        while angle < max_angle:
            angler = radians(angle)
            x = int(start.x + length * cos(angler))
            y = int(start.y + length * sin(angler))
            angle += 3
            if (ox == x and oy == y) or not self.check_point(x, y):
                continue
            ox, oy = x, y
            pop = pmap[x][y]
            if pop > old_pop:
                new_point = Point(x, y, hmap[x][y])
                old_pop = pop
        return new_point


class LocalConstraints(object):
    def __init__(self):
        pass

    def close(self, p1, p2):
        return p1.distance(p2) < settings.MAINROAD_SEGMENT_LENGTH

    def ajust_point(self, point):
        if not point:
            return None
        return point


class RoadGuesser(object):
    def __init__(self, hmap, hlim, pmap):
        self.goals = GlobalGoals(hmap, hlim, pmap)
        self.constraints = LocalConstraints()
        self.segments = []
        self.roads = []

    def add_point(self, point):
        query = []
        done = []
        goals = self.goals
        road = RoadSegment(point, query)
        query.append(road)
        while query:
            for road in query[:]:
                road.generate_next(self.goals, self.constraints)
                if road.fail:
                    query.remove(road)
                if road.done:
                    done.append(road)
                    query.remove(road)
        self.segments.extend(done)



class ModMainRoads(Module):

    def __init__(self):
        self.map = None

    def process(self, map_obj):
        self.map = map_obj
        print "Generating roads."
        self.planRoads()

    def planRoads(self):
        proto = self.map
        roads = []
        g = RoadGuesser(proto.heights, (proto.height_max,
                            proto.height_min), proto.population)
        for center in list(proto.main_cbd):
            g.add_point(center.point)
        proto.roads = g.segments

def get_module():
    return ModMainRoads()

