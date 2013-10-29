#import multiprocessing
from threading import Thread
from Queue import Queue


class Processor(object):

    num_procs = 50

    def __init__(self):
        self.q = q = Queue() #multiprocessing.JoinableQueue()
        self.procs = procs = []
        self.processing = False
        for i in range(self.num_procs):
            nameStr = 'Worker_'+str(i)
            p = Thread(target=self.worker, args=(q,nameStr))
            p.daemon = True
            p.start()
            procs.append(p)

    def worker(self, q, nameStr):
        print 'Worker %s started' %nameStr
        pr = self.processing
        while True:
            item = q.get()
            if item is None: # detect sentinel
                break
            item()
            if pr:
                print q.qsize()
            q.task_done()
        print 'Worker %s Finished' % nameStr
        q.task_done()

    def extend(self, array):
        q = self.q
        self.processing = False
        count = len(array)
        percent = 0.0
        for index, item in enumerate(array):
            q.put(item)
            p = int(float(index) / count * 100)
            if p != percent:
                percent = p
                print percent
        print "Adding done. {0} items in queue left".format(q.size())
        self.processing = True

    def join(self):
        for i in range(self.num_procs):
            # send termination sentinel, one for each process
            self.q.put(None)
        for p in self.procs:
            p.join()
