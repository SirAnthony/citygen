#!/usr/bin/python
import sys
import matplotlib.pyplot as plt

infile = sys.argv[1]

with open(infile) as inf:
    points = []
    lines = []
    for line in inf:
        line = line.strip().rstrip('\n')
        try:
            tag, data = line.split(None, 1)
        except:
            continue
        if tag == 'point':
            points.append(data.split(':')[:2])
        elif tag == 'line':
            line = zip(*[x.split(':')[:2] for x in data.split()])
            plt.plot(*line, color="black")
    if len(points):
        points = zip(*points)
        plt.plot(points[0], points[1], 'ro')
    plt.show()
