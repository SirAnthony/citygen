
from .module import Module
from .. import settings


class ModPopulation(Module):

    def __init__(self):
        self.map = None

    def process(self, map_obj):
        self.map = map_obj

        self.fillMap()



    def fillMap(self):
        proto = self.map







def get_module():
    return ModPopulation()
