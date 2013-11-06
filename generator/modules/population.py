
from .module import Module
from ..geom import LightCenter
from .. import settings
from math import exp, sqrt
from multiprocessing import Pool, Value, Array
from PIL import Image
import hashlib
import numpy as np
import sys


shared_pop = Array('d',
        settings.GENERATOR_SIZE_W * settings.GENERATOR_SIZE_H)


class Calculator(object):
    def __init__(self, centers, hmap, hmax, hmin):
        self.centers = centers
        self.heights = hmap
        # + 0.01 percent for the seafront
        self.hwater = (settings.GENERATOR_WATER - 0.01) * (hmax - hmin) + hmin

    def dist_to_center(self, x, y, c):
        return sqrt((x - c.point.x) ** 2 + (y - c.point.y) ** 2)

    def param_A(self, center):
        """ Formula for the 'A' coefficient. This is center influence.
The ability of center to influence densities."""
        return 10000.0 * center.proximity

    def param_b(self, x, y):
        """ Formula for the 'b' coefficient. This is influence of city
geography and can be described as land cost."""
        #TODO: distance between
        return 0.9

    def popFunc(self, x, y, centers, A, b, d, max_dist):
        pop = 0
        res_b = -b(x, y)
        ratio = 1.0 # float(settings.GENERATOR_SIZE_H)
        for center in centers:
            dr = d(x, y, center)
            if dr > max_dist:
                continue
            # negative exponent
            pop += A(center) * exp(res_b * dr / max_dist)
        return pop

    def __call__(self, x):
        target = shared_pop
        D = self.popFunc
        A = self.param_A
        b = self.param_b
        d = self.dist_to_center
        centers = self.centers
        xpos = x * settings.GENERATOR_SIZE_W
        max_dist = settings.POPULATION_CENTER_SIZE
        hwater = self.hwater
        heights = self.heights
        for y in range(0, settings.GENERATOR_SIZE_H):
            if heights[x][y] < hwater:
                continue
            target[xpos + y] = D(x, y, centers, A, b, d, max_dist)


class ModPopulation(Module):

    def __init__(self):
        self.map = None

    def get_hash(self):
        proto = self.map
        m = hashlib.md5()
        #for c in sorted(map(lambda x: x.hash(), proto.centers)):
        #    m.update(c)
        for item in (proto.seed, settings.GENERATOR_SIZE_W,
                     settings.GENERATOR_SIZE_H,
                     settings.POPULATION_CENTER_SIZE,
                     settings.GENERATOR_WATER):
            m.update(str(item))
        return m.hexdigest()

    def process(self, map_obj):
        self.map = map_obj

        pop_map = self.load()
        if pop_map is None:
            pop_map = self.fillMap()
            self.dump(pop_map)

        self.map.population = pop_map


    def fillMap(self):
        proto = self.map

        print "Filling population map. It may take a while on the big map."
        for i in range(0,
                settings.GENERATOR_SIZE_W * settings.GENERATOR_SIZE_H):
            shared_pop[i] = 0

        pool = Pool(settings.POOLS_COUNT)
        xcount = settings.GENERATOR_SIZE_W
        del_sign = "\b" * 50
        centers = map(lambda c: LightCenter(c), proto.business_centers)
        for i, _ in enumerate(pool.imap_unordered(
                    Calculator(centers, proto.heights,
                    proto.height_max, proto.height_min),
                    xrange(xcount)), 1):
            rate = float(i) / float(xcount)
            sys.stdout.write("{0}[{1:<30}]\t{2}%".format(del_sign,
                        "=" * int(30 *  rate), rate * 100.0))
            sys.stdout.flush()
        print "{0}Generation done.{1}".format(del_sign, " " * 50)

        return np.frombuffer(shared_pop.get_obj()).reshape(
                (settings.GENERATOR_SIZE_H, settings.GENERATOR_SIZE_W))

    def load(self):
        print "Loading population map cache."
        filehash = self.get_hash()
        try:
            arr = np.load("cache/pop_{0}.npy".format(filehash))
        except IOError:
            print "Loading was unsuccessful. Generating new."
            arr = None
        return arr

    def dump(self, data):
        print "Saving population map cache."
        max_pop = data.max()
        filehash = self.get_hash()
        np.save("cache/pop_" + filehash, data)
        prepared_data = (data * 255.0/max_pop).astype('uint8')
        img = Image.fromarray(prepared_data)
        img.save("pop_{0}.png".format(filehash))


def get_module():
    return ModPopulation()
