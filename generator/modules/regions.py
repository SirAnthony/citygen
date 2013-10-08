

from .module import Module
from .. import settings





class ModRegions(Module):

    def __init__(self):
        self.map = None

    def process(self, map_obj):
        self.map = map_obj

        print "Guessing regions..."
        self.guessRegions()


    def guessRegions(self):
        proto = self.map

        max_pr = max(proto.centers, key=lambda x: x.proximity).proximity
        min_pr = min(proto.centers, key=lambda x: x.proximity).proximity
        pr_treshhold = max_pr * settings.REGIONS_BUISNESS_TRESHHOLD

        buisness_regions = filter(lambda x: x.proximity > pr_treshhold \
                                    and not x.water, proto.centers)

        if not buisness_regions:
            raise Exception("Regions treshhold is too high")

        def trade_path_dist(center):
            dist = []
            new_neighbors = neighbors + list(center.neighbors)
            new_neighbors.append(center)
            for n in center.neighbors:
                if n in neighbors:
                    continue
                if n.ocean:
                    return 1.0
                dist.append(0.5 * trade_path_dist(n, new_neighbors))
            return max(dist) if dist else 0.0

        #for center in buisness_regions:
            #print trade_path_dist(center)



def get_module():
    return ModRegions()
