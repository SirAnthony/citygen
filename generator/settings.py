
from math import log
SEED_STRING=None
GENERATOR_NUM_POINTS = 1000
GENERATOR_SIZE_W = 500
GENERATOR_SIZE_H = 500
NUM_LLOYD_ITERATIONS = 3
GENERATOR_ISLAND = False
GENERATOR_LAKE_THRESHOLD = 0.8
GENERATOR_WATER = 0.3
WEIGHT_WIDTH = 5
REGIONS_BUSINESS_TRESHHOLD = 0.8
REGIONS_BUSINESS_MAX = int(log(GENERATOR_NUM_POINTS, 2)) + 1
if REGIONS_BUSINESS_MAX <= 0:
    REGIONS_BUSINESS_MAX = 1
POPULATION_CENTER_SIZE = float(GENERATOR_SIZE_W) / 4.0

POOLS_COUNT = 7

MAINROAD_SEGMENT_ANGLE = 20
MAINROAD_SEGMENT_LENGTH = 10
