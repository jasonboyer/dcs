#!/usr/bin/env python
# Adapted from http://pybrain.org/docs/tutorial/reinforcement-learning.html

from __future__ import print_function

import boto.sqs.message
from boto.sqs.message import MHMessage
from hub import constants
import pprint
import re
from rl.agent import DogAgent
from rl.dogenv import DogEnv
from rl.quietdogtask import QuietDogTask
from scipy import mean
import sys

from scipy import *
import sys, time
import pylab

from pybrain.rl.environments.mazes import Maze, MDPMazeTask
from pybrain.rl.learners.valuebased import ActionValueTable
from pybrain.rl.agents import LearningAgent
from pybrain.rl.learners import Q, QLambda, SARSA #@UnusedImport
from pybrain.rl.explorers import BoltzmannExplorer #@UnusedImport
from pybrain.rl.experiments import Experiment
from pybrain.rl.environments import Task
import threading

pp = pprint.PrettyPrinter()

class RlOp(threading.Thread):
    episodes = 1
    epilen = 200
    def __init__(self, event_queue_name, hub_queue_name):
        super().__init__()
        # create environment
        self.conn = boto.sqs.connect_to_region(constants.REGION)
        self.event_queue = self.conn.get_queue(event_queue_name)
        self.event_queue.set_message_class(MHMessage)
        self.env = DogEnv(DogEnv.ALL_QUIET, DogEnv.ALL_QUIET, self.event_queue, hub_queue_name)
        self.env.delay = (self.episodes == 1)

        # create task
        self.task = QuietDogTask(self.env)

        # create value table and initialize with ones
        # TODO: Get number of states from DogEnv
        self.table = ActionValueTable(2*5*4, 5*4)
        self.table.initialize(1.)

        # create agent with controller and learner - use SARSA(), Q() or QLambda() here
        self.learner = SARSA()

        # standard exploration is e-greedy, but a different type can be chosen as well
        self.learner.explorer = BoltzmannExplorer()

        # create agent
        self.agent = DogAgent(self.table, self.learner)

        # create experiment
        self.experiment = Experiment(self.task, self.agent)

    def run(self):
        self.call_run()

    def call_run(self):
        print('RlOp: running')
        # prepare plotting
        pylab.gray()
        pylab.ion()

        for i in range(1000):

            # interact with the environment (here in batch mode)
            self.experiment.doInteractions(100)
            self.agent.learn()
            self.agent.reset()

            results0 = self.table.params.reshape(2, 4, 5, 20)[0]
            results1 = self.table.params.reshape(2, 4, 5, 20)[1]
            pp.pprint(results0.argmax(2))
            pp.pprint(results1.argmax(2))

            # and draw the table
            #ar=self.table.params.reshape(2,5,4,5,4)
            #for state1 in range(len(constants.SOUNDS)):
            #    for state2 in range(4):
            #        pylab.pcolor(ar[1][state1][state2])
            #        pylab.draw()

        results0 = self.table.params.reshape(2, 4, 5, 20)[0]
        results1 = self.table.params.reshape(2, 4, 5, 20)[1]
        while True:
            time.sleep(60)
            pp.pprint(results0.argmax(2))
            pp.pprint(results1.argmax(2))

if __name__ == '__main__':
    conn = boto.sqs.connect_to_region(constants.REGION)
    p = re.compile('\.')
    test_queue = conn.create_queue('test_queue'.join(p.split(str(time.time()))))
    test_queue.set_message_class(MHMessage)
    rlop = RlOp(test_queue)
#    rlop.start()
#    time.sleep(1)
    for k in range(15):
        for i in range(100):
            bark_mess = MHMessage(test_queue)
            bark_mess[constants.ATTR_DOG_STATE] = constants.DOG_STATE_QUIET
            test_queue.write(bark_mess)

        for i in range(100):
            bark_mess = MHMessage(test_queue)
            bark_mess[constants.ATTR_DOG_STATE] = constants.DOG_STATE_BARKING
            test_queue.write(bark_mess)

    rlop.call_run()

    conn.delete_queue(test_queue, force_deletion=True)
    print('Done')
