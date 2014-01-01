from utils import load_func, dump_func
import logging

class TaskContext:
    def __init__(self, stageId, splitId, attemptId):
        self.stageId = stageId
        self.splitId = splitId
        self.attemptId = attemptId

class TaskResult:
    def __init__(self, value, accumUpdates):
        self.value = value
        self.accumUpdates = accumUpdates

class Task:
    nextId = 0
    @classmethod
    def newId(cls):
        cls.nextId += 1
        return cls.nextId

    def run(self, id):
        raise NotImplementedError
    def preferredLocations(self):
        raise NotImplementedError
    def generation(self):
        raise NotImplementedError
    
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['func']
        return d, dump_func(self.func)

    def __setstate__(self, state):
        self.__dict__, code = state
        self.func = load_func(code, globals())

class DAGTask(Task):
    def __init__(self, stageId):
        self.id = self.newId()
        self.stageId = stageId
        #self.gen = env.mapOutputTracker.getGeneration
    
    def generation(self):
        return self.gen

class ResultTask(DAGTask):
    def __init__(self, stageId, rdd, func, partition, locs, outputId):
        DAGTask.__init__(self, stageId)
        self.rdd = rdd
        self.func = func
        self.partition = partition
        self.split = rdd.splits[partition]
        self.locs = locs
        self.outputId = outputId

    def run(self, attemptId):
        context = TaskContext(self.stageId, self.partition, attemptId)
        return self.func(context, self.rdd.iterator(self.split))

    def preferredLocations(self):
        return self.locs

    def __hash__(self):
        return self.rdd.id * 99999 + self.partition

    def __str__(self):
        return "ResultTask(%d, %d)" % (self.stageId, self.partition)

    def __repr__(self):
        return str(self)

class ShuffleMapTask(DAGTask):
    def __init__(self, stageId, rdd, dep, partition, locs):
        DAGTask.__init__(self, stageId)
        self.stageId = stageId
        self.rdd = rdd
        self.dep = dep
        self.partition = partition
        self.split = rdd.splits[partition]
        self.locs = locs

    def run(self, attempId):
        pass
