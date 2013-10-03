
from .module import Module
from ..geom import (Point, LineSegment, Center, Edge, Corner,
                            interpolate)
from .. import settings
from scipy.spatial import Voronoi, Delaunay
from random import randrange


def next_p2(n):
    if ( 1 << n.bit_length() - 1) == n:
        return n
    return 1 << n.bit_length()


class ShapeGenerator(object):
    def __init__(self, stype=None):
        self.func = self.height_default

    def perlin(self, q):
        #c = glm::perlin( glm::vec2( q.x , q.y ) )
        #l = length( q )
        #return c < ( 0.2 + 0.3 * l * l )
        pass

    @staticmethod
    def height_default(x, y, d, h):
        precision = 0.01
        r = 0.5 # roughness
        f = 1 / precision
        return h + randrange(-r*f, r*f) / f * d


    def square(self, x, y, d):
        fsum, num = 0.0, 0
        if 0 <= (x - d):
            fsum += self.data[x - d][y]
            num += 1
        if (x + d) < self.width:
            fsum += self.data[x + d][y]
            num += 1
        if 0 <= (y - d):
            fsum += self.data[x][y - d]
            num += 1
        if (y + d) < self.height:
            fsum += self.data[x][y + d]
            num += 1
        self.data[x][y] = self.func(x, y, d, fsum/num)


    def diamond(self, x, y, d):
        fsum, num = 0.0, 0
        if 0 <= (x - d):
            if 0 <= (y - d):
                fsum += self.data[x - d][y - d]
                num += 1
            if (y + d) < self.height:
                fsum += self.data[x - d][y + d]
                num += 1
        if (x + d) < self.width:
            if 0 <= (y - d):
                fsum += self.data[x + d][y - d]
                num += 1
            if (y + d) < self.height:
                fsum += self.data[x + d][y + d]
                num += 1
        self.data[x][y] = self.func( x, y, d, fsum / num )


    def diamondSquare(self, proto):
        self.width = next_p2(proto.width)
        self.height = next_p2(proto.height)
        d = self.width if self.width < self.height else self.height
        self.data = dict(enumerate([dict() for i in range(0, d)]))

        self.data[0][0] = self.func(0, 0, d, 0)
        self.data[0][d-1] = self.func(0, d, d, 0)
        self.data[d-1][0] = self.func(d, 0, d, 0)
        self.data[d-1][d-1] = self.func(d, d, d, 0)

        d = d/2
        # perform square and diamond steps
        while 1 <= d:
            d2 = 2*d
            for x in range(d, self.width, d2):
                for y in range(d, self.height, d2):
                    self.diamond(x, y, d)
            for x in range(d, self.width, d2):
                for y in range(0, self.height, d2):
                    self.square(x, y, d)
            for x in range(0, self.width, d2):
                for y in range(0, self.height, d2):
                    self.diamond(x, y, d)
            for x in range(0, self.width, d2):
                for y in range(d, self.height, d2):
                    self.square(x, y, d)
            d = d/2

        # Find minimum & maximum
        max_height = 1;
        min_height = 0;
        for x in range(0, self.width):
            for y in range(0, self.height):
                d = self.data[x][y]
                if d > max_height:
                    max_height = d
                elif d < min_height:
                    min_height = d

        proto.height_max = max_height
        proto.height_min = min_height
        proto.heights = self.data


class ModShape(Module):

    def __init__(self):
        self.map = None
        self.heights = None


    def process(self, map_obj):
        self.map = map_obj

        # Function to make water
        self.shape = lambda x: True

        print "Building height map."
        # Generate heightmap for new location
        self.generateHeightMap()
        self.assignElevation( )

        # Determine polygon and corner type: ocean, coast, land.
        self.assignOceanCoastAndLand()

        #~ // Rescale elevations so that the highest is 1.0, and they're
        #~ // distributed well. We want lower elevations to be more common
        #~ // than higher elevations, in proportions approximately matching
        #~ // concentric rings. That is, the lowest elevation is the
        #~ // largest ring around the island, and therefore should more
        #~ // land area than the highest elevation, which is the very
        #~ // center of a perfectly circular island.
        #~ //redistributeElevations( cnrs );
        #~
        #~ // Assign elevations to non-land corners
        #~ //Corner* q;
        #~ //FOREACH1( q, corners ) {
        #~ //   if( q->ocean || q->coast )
        #~ //       q->elevation = 0.0;
        #~ //}

        # Polygon elevations are the average of their corners
        self.assignPolygonElevations()

        # Determine downslope paths.
        self.calculateDownslopes()


    def generateHeightMap(self):
        gen = ShapeGenerator()
        gen.diamondSquare(self.map)

    def assignElevation(self):
        # TODO: for more realistic landscape with smooth valleys and rough peaks
        # we need to generate 2 maps, normalize it and multiply.
        proto = self.map
        for q in proto.corners:
            x, y = int(q.point.x), int(q.point.y)
            q.elevation = ( proto.heights[x][y] - proto.height_min ) / (
                            proto.height_max - proto.height_min )

    def assignOceanCoastAndLand(self):
        proto = self.map

        # Set the map water
        queue = []
        for p in proto.centers:
            numWater = 0
            for q in p.corners:
                if q.elevation < settings.GENERATOR_WATER:
                    q.water = True
                if q.border and settings.GENERATOR_ISLAND:
                    p.border = True
                    p.ocean = True
                    q.water = True
                    queue.append(p)
                if q.water:
                    numWater += 1
            p.water = (p.ocean or numWater >= ( len(p.corners) *
                        settings.GENERATOR_LAKE_THRESHOLD))

        while queue:
            p = queue.pop()
            for r in p.neighbors:
                if p.ocean and r.water and not r.ocean:
                    r.ocean = True
                    queue.append(r)


        # Set the polygon attribute 'coast' based on its neighbors. If
        # it has at least one ocean and at least one land neighbor,
        # then this is a coastal polygon.
        for p in proto.centers:
            numOcean = 0
            numLand = 0
            for n in p.neighbors:
                numOcean += int(n.ocean)
                numLand += int(n.water)
            p.coast = (numOcean > 0) and (numLand > 0)

        # Set the corner attributes based on the computed polygon
        # attributes. If all polygons connected to this corner are
        # ocean, then it's ocean; if all are land, then it's land;
        # otherwise it's coast.
        for q in proto.corners:
            numOcean = 0
            numLand = 0
            for p in q.touches:
                numOcean += int(p.ocean)
                numLand += int(not p.water)
            q.ocean = bool(numOcean == len(q.touches))
            q.coast = (numOcean > 0) and (numLand > 0)
            q.water = q.border or ((numLand != len(q.touches)) and \
                        not q.coast)


    def assignPolygonElevations(self):
        heights = self.map.heights
        def get_z(point):
            return heights[int(point.x)][int(point.y)];

        for p in self.map.centers:
            p.point.z = get_z(p.point)
            sumElevation = sum([e.elevation for e in p.corners])
            if sumElevation:
                p.elevation = float(sumElevation) / float(len(p.corners))

        for e in self.map.edges:
            if e.midpoint:
                e.midpoint.z = get_z(e.midpoint)

        for c in self.map.corners:
            c.point.z = get_z(c.point)


    def calculateDownslopes(self):
        for q in self.map.corners:
            r = q
            for s in q.adjacent:
                if s.elevation <= r.elevation:
                    r = s
            q.downslope = r


def get_module():
    return ModShape()
