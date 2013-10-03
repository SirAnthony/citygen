
from .modules import MODULES_AVAILABLE
from .map import Map

def import_module(name):
    return getattr(__import__('generator.modules', fromlist=[name],
                                                        level=-1), name)

class Generator:



    def __init__(self, modules=MODULES_AVAILABLE):
        self.modules = [m.get_module() for m in [
                import_module(x) for x in filter(
                    lambda x: x in MODULES_AVAILABLE, modules)]]

    def newMap(self, seed_string=None):
        print "Preparing map..."
        self.map = Map(seed_string)

    def runStages(self):
        for module in self.modules:
            module.process(self.map)

    def generate(self):
        self.newMap()
        self.runStages()
        print "Output..."
        with open('out.pts', 'w') as pts:
            pts.write(self.map.out())
        with open('out.poly', 'w') as poly:
            poly.write(self.map.out_polygons())
