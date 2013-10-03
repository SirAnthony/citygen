
from ..geom import (Point, LineSegment, Center, Edge, Corner,
                            interpolate)
from .module import Module
from .. import settings
from scipy.spatial import Voronoi, Delaunay
from random import randrange


class ModGraph(Module):

    def __init__(self):
        self.map = None
        self.heights = None


    def process(self, map_obj):
        self.map = map_obj

        print "Place points..."
        points = self.generateRandomPoints()

        print "Improve points..."
        points = self.improveRandomPoints(points)

        # Create a graph structure from the Voronoi edge list. The
        # methods in the Voronoi object are somewhat inconvenient for
        # my needs, so I transform that data into the data I actually
        # need: edges connected to the Delaunay triangles and the
        # Voronoi polygons, a reverse map from those four points back
        # to the edge, a map from these four points to the points
        # they connect to (both along the edge and crosswise).

        print "Build graph..."
        self.buildGraph(points)
        self.improveCorners()

        # Remove absent nodes
        self.sweepGraph()


    def generateRandomPoints(self):
        points = []
        for i in range(0, settings.GENERATOR_NUM_POINTS):
            points.append([
                randrange(10.0, settings.GENERATOR_SIZE_W - 10.0),
                randrange(10.0, settings.GENERATOR_SIZE_H - 10.0),
            ])
        return points


    def improveRandomPoints(self, points):
        # We'd really like to generate "blue noise". Algorithms:
        #  1. Poisson dart throwing: check each new point against all
        #     existing points, and reject it if it's too close.
        #  2. Start with a hexagonal grid and randomly perturb points.
        #  3. Lloyd Relaxation: move each point to the centroid of the
        #     generated Voronoi polygon, then generate Voronoi again.
        #  4. Use force-based layout algorithms to push points away.
        #  5. More at http://www.cs.virginia.edu/~gfx/pubs/antimony/
        #  Option 3 is implemented here. If it's run for too many iterations,
        #  it will turn into a grid, but convergence is very slow, and we only
        #  run it a few times.

        def voronoi_avg_point(voronoi, index):
            rindex = voronoi.point_region[index]
            region = voronoi.regions[rindex]
            p = [0, 0]
            for pindex in region:
                q = voronoi.vertices[pindex]
                p[0] += q[0]
                p[1] += q[1]
            region_size = len(region)
            return [p[0]/region_size, p[1]/region_size]

        #Delaunay::Rectangle size( 0, 0, GENERATOR_SIZE, GENERATOR_SIZE );
        for i in range(0, settings.NUM_LLOYD_ITERATIONS):
            voronoi = Voronoi(points)
            for pindex in range(0, len(points)):
                points[pindex] = voronoi_avg_point(voronoi, pindex)
        return filter(lambda p: \
            0 <= p[0] < settings.GENERATOR_SIZE_W and \
            0 <= p[1] < settings.GENERATOR_SIZE_H, points)

    def buildGraph(self, points):
        proto = self.map

        #Delaunay::Rectangle r( 0, 0, GENERATOR_SIZE, GENERATOR_SIZE );
        voronoi = Voronoi(points)
        delaunay = Delaunay(points)

        #std::map< float, std::map< float, Center* > > centerLookup;
        centerLookup = {}

        # Build Center objects for each of the points, and a lookup map
        # to find those Center objects again as we build the graph
        for point in points:
            p = Center(len(proto.centers))
            p.point = Point(*point)
            proto.centers.add(p)
            (px, py) = point
            if px not in centerLookup.keys():
                centerLookup[px] = {}
            centerLookup[px][py] = p

        # The Voronoi library generates multiple Point objects for
        # corners, and we need to canonicalize to one Corner object.
        # To make lookup fast, we keep an array of Points, bucketed by
        # x value, and then we only have to look at other Points in
        # nearby buckets. When we fail to find one, we'll create a new
        # Corner object.
        #std::map< int, std::vector< Corner* > > _cornerMap;
        _cornerMap = {}

        def check_point(p):
            if not p:
                return None
            # I cannot find bounadries for voronoi in scipy
            w = settings.GENERATOR_SIZE_W
            h = settings.GENERATOR_SIZE_H
            if not (-1 < p.x <= w) or not (-1 < p.y <= h):
                return None
            return p

        def get_delaunay_segment(voronoi, index):
            pi = voronoi.ridge_points[index]
            p0 = check_point(
                Point(*voronoi.points[pi[0]])) if pi[0] >= 0 else None
            p1 = check_point(
                Point(*voronoi.points[pi[1]])) if pi[1] >= 0 else None
            # I cannot find bounadries for voronoi in scipy
            return LineSegment(p0, p1)

        def get_voronoi_segment(voronoi, index):
            pi = voronoi.ridge_vertices[index]
            v0 = check_point(
                Point(*voronoi.vertices[pi[0]])) if pi[0] >= 0 else None
            v1 = check_point(
                Point(*voronoi.vertices[pi[1]])) if pi[1] >= 0 else None
            return LineSegment(v0, v1)

        def makeCorner(point):
            if not point:
                return

            for bucket in range(int(point.x) - 1, int(point.x) + 2):
                if bucket not in _cornerMap:
                    _cornerMap[bucket] = set()
                for q in _cornerMap[bucket]:
                    dx = point.x - q.point.x
                    dy = point.y - q.point.y
                    if (dx * dx + dy * dy) < 1e-6:
                        return q

            bucket = int(point.x)
            q = Corner(len(proto.corners))
            proto.corners.add(q)
            q.setPoint(point)
            _cornerMap[bucket].add(q)
            return q


        for index in range(0, len(voronoi.ridge_vertices)):
            dedge = get_delaunay_segment(voronoi, index)
            vedge = get_voronoi_segment(voronoi, index)

            # Fill the graph data. Make an Edge object corresponding to
            # the edge from the voronoi library.
            edge = Edge(len(proto.edges))
            proto.edges.add(edge)

            if vedge.p0 and vedge.p1:
                edge.midpoint = interpolate(vedge.p0, vedge.p1, 0.5)
            edge.v0 = makeCorner(vedge.p0)
            edge.v1 = makeCorner(vedge.p1)
            if dedge.p0:
                edge.d0 = centerLookup[dedge.p0.x][dedge.p0.y];
            if dedge.p1:
                edge.d1 = centerLookup[dedge.p1.x][dedge.p1.y];
            edge.register()


    def improveCorners(self):
        #std::map< int, s2f > newCorners;
        newCorners = {}

        # First we compute the average of the centers next to each corner.
        for q in self.map.corners:
            point = q.point
            if not q.border:
                point = Point(0, 0)
                size = len(q.touches)
                for r in q.touches:
                    point.x += r.point.x
                    point.y += r.point.y
                point.x /= size
                point.y /= size
            newCorners[q.index] = q.point

        # Move the corners to the new locations.
        for corner in self.map.corners:
            corner.point = newCorners[corner.index]

        # The edge midpoints were computed for the old corners and need
        # to be recomputed.
        for edge in self.map.edges:
            if edge.v0 and edge.v1:
                edge.midpoint = interpolate(edge.v0.point, edge.v1.point, 0.5)


    def sweepGraph(self):
        targets = []
        for c in self.map.centers:
            targets.extend([c.neighbors, c.borders, c.corners])

        for q in self.map.corners:
            targets.extend([q.touches, q.protrudes, q.adjacent])

        for tgt in targets:
            try:
                tgt.remove(None)
            except:
                pass


def get_module():
    return ModGraph()
