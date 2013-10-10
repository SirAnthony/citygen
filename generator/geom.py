
from . import settings
from collections import defaultdict
import math


class Point(object):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.z = 0

    def distance(self, pt):
        return math.sqrt((pt.x - self.x) ** 2 +
                         (pt.y - self.y) ** 2)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"{0.x}:{0.y}:{0.z}".format(self)


class LineSegment(object):

    def __init__(self, p0, p1):
        if p0 and not isinstance(p0, Point) or \
           p1 and not isinstance(p1, Point):
            raise TypeError("Must be Point object")
        self.p0 = p0
        self.p1 = p1

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"line {0.p0} {0.p1}".format(self)


class Center(object):

    def __init__(self, index):
        self.index = index
        self.point = Point()     # location
        self.water = False       # lake or ocean
        self.ocean = False       # ocean
        self.coast = False       # land polygon touching an ocean
        self.border = False      # at the edge of the map
        self.proximity = 0.0     # average proximity to other centers
        self.elevation = 0.0     # 0.0-1.0
        self.moisture = 0.0      # 0.0-1.0
        self.temperature = 26    # Node temperature
        self.weight = defaultdict(int)   # weights of centers

        self.neighbors = set()      # list<Center*>
        self.borders = set()        # list<Edge*>
        self.corners = set()        # list<Corner*>


    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"center {0.index}\n\tpoint {0.point}".format(self)


class Edge(object):

    def __init__(self, index):
        self.index = index
        self.d0 = None   # Delaunay edge Center*
        self.d1 = None   # Delaunay edge Center*
        self.v0 = None   # Voronoi edge Corner*
        self.v1 = None   # Voronoi edge Corner*
        self.midpoint = Point()  # halfway between v0,v1
        self.river = 0   # volume of water, or 0

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        if self.v0 and self.v1:
            return u"Edge {0.index}\n\tline {0.v0.point} {0.v1.point}".format(self)
        return u"Edge {0.index}\n"

    def register(self):
        # Centers point to edges. Corners point to edges.
        if self.d0:
            self.d0.borders.add(self)
        if self.d1:
            self.d1.borders.add(self)
        if self.v0:
            self.v0.protrudes.add(self)
        if self.v1:
            self.v1.protrudes.add(self)

        # Centers point to centers.
        if self.d0 and self.d1:
            self.d0.neighbors.add(self.d1)
            self.d1.neighbors.add(self.d0)

        # Corners point to corners
        if self.v0 and self.v1:
            self.v0.adjacent.add(self.v1)
            self.v1.adjacent.add(self.v0)

        # Centers point to corners
        for d in (self.d0, self.d1):
            if not d: continue
            d.corners.add(self.v0)
            d.corners.add(self.v1)

        # Corners point to centers
        for v in (self.v0, self.v1):
            if not v: continue
            v.touches.add(self.d0)
            v.touches.add(self.d1)



class Corner(object):

    def __init__(self, index):
        self.index = index
        self.point = Point()     # location
        self.water = False       # lake or ocean
        self.ocean = False       # ocean
        self.coast = False       # land polygon touching an ocean
        self.border = False      # at the edge of the map
        self.elevation = 0.0     # 0.0-1.0
        self.moisture = 0.0      # 0.0-1.0
        self.temperature = 26    # Node temperature
        self.proximity = 0.0     # average proximity to nearest centers

        self.touches = set()        # list<Center*>
        self.protrudes = set()      # list<Edge*>
        self.adjacent = set()       # list<Corner*>

        self.river = 0           # 0 if no river, or volume of water in river
        self.downslope = None    # Corner* pointer to adjacent corner most downhill
        self.watershed = None    # Corner* pointer to coastal corner, or null
        self.watershed_size = 0

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"Corner {0.index}\n\tpoint {0.point}".format(self)


    def setPoint(self, p):
        self.point = Point(p.x, p.y)
        self.border = bool(p.x == 0 or
                       p.x == settings.GENERATOR_SIZE_W or
                       p.y == 0 or
                       p.y == settings.GENERATOR_SIZE_H)


def interpolate(p0, p1, delta):
    if not isinstance(p0, Point) or not isinstance(p1, Point):
            raise TypeError("Must be Point object")
    return Point(p0.x + delta  * ( p1.x - p0.x ),
        p0.y + delta  * ( p1.y - p0.y ))
