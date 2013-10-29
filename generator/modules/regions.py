

from .module import Module
from .. import settings

REGION_TYPES = {
    "None": 0,
    "Business": 1,
    "Private": 2,
}



class ModRegions(Module):

    def __init__(self):
        self.map = None

    def process(self, map_obj):
        self.map = map_obj

        print "Guessing regions..."
        self.guessRegions()
        self.expandRegions()
        self.fillUnassigned()


    def guessRegions(self, weight_param="water"):
        proto = self.map

        max_pr = max(proto.centers, key=lambda x: x.proximity).proximity
        min_pr = min(proto.centers, key=lambda x: x.proximity).proximity
        pr_treshhold = max_pr - max_pr * settings.REGIONS_BUSINESS_TRESHHOLD

        business_regions = filter(lambda x: x.proximity < pr_treshhold \
                                    and not x.water, proto.centers)
        if not business_regions:
            raise Exception("Regions treshhold is too high")

        # Limit centers
        sort_func = lambda x: (x.weight[weight_param], 1/x.proximity)
        business_regions.sort(key=sort_func, reverse=True)

        regions = []

        def check_neighboards(center, processed=[], depth=0):
            if center in processed or depth > 4:
                return False
            depth += 1
            if center in regions:
                return True
            new_processed = [center]
            new_processed.extend(processed)
            for n in center.neighbors:
                if check_neighboards(n, new_processed, depth):
                    return True
            return False

        for r in business_regions:
            if not check_neighboards(r):
                regions.append(r)

        proto.business_centers = regions[:settings.REGIONS_BUSINESS_MAX]


    def expandRegions(self, weight_param="water"):
        proto = self.map
        sort_func = lambda x: (x.weight[weight_param], 1/x.proximity)
        processed = set()
        proto.main_cbd = set(proto.business_centers)


        def choose_regions(rlist, func, treshhold, srt=sort_func):
            rlist.sort(key=srt, reverse=True)
            regions = []
            for item in rlist:
                if func(item) < treshhold:
                    break
                regions.append(item)
            return regions

        def watch_neighbors(center, func, treshhold):
            if center in processed:
                return
            processed.add(center)
            center.region_type = REGION_TYPES["Business"]
            n = list(center.neighbors)
            regions = choose_regions(n, func, treshhold)
            proto.business_centers.extend(regions)
            for r in regions:
                watch_neighbors(r, func, treshhold)

        # Expand regions
        for r in proto.main_cbd:
            max_weight = max(r.neighbors, key=lambda x: \
                            x.weight[weight_param]).weight[weight_param]
            min_weight = min(r.neighbors, key=lambda x: \
                            x.weight[weight_param]).weight[weight_param]
            l, tr = None, None
            if max_weight != min_weight:
                l = lambda x: x.weight[weight_param]
                tr = max_weight * settings.REGIONS_BUSINESS_TRESHHOLD
            else:
                max_pr = max(r.neighbors, key=lambda x: x.proximity).proximity
                l = lambda x: 1/x.proximity
                tr = 1 / ( max_pr * settings.REGIONS_BUSINESS_TRESHHOLD )
            watch_neighbors(r, l, tr)

        proto.business_centers = set(proto.business_centers)


    def fillUnassigned(self):
        for region in self.map.centers:
            if not hasattr(region, 'region_type'):
                region.region_type = 0
            for q in region.corners:
                q.region_type = region.region_type


def get_module():
    return ModRegions()
