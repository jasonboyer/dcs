#!/usr/bin/env python
# Adapted from http://pybrain.org/docs/tutorial/reinforcement-learning.html

from __future__ import print_function

###########################################################################
# This program takes 4 parameters at the command line and runs the
# (single) cartpole environment with it, visualizing the cart and the pole.
# if cart is green, no penalty is given. if the cart is blue, a penalty of
# -1 per step is given. the program ends with the end of the episode. if
# the variable "episodes" is changed to a bigger number, the task is executed
# faster and the mean return of all episodes is printed.
###########################################################################

import boto.sqs.message
from boto.sqs.message import MHMessage
from hub import constants
from pybrain.tools.shortcuts import buildNetwork
from pybrain.rl.agents.learning import LearningAgent
from pybrain.rl.experiments import EpisodicExperiment
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

#if len(sys.argv) < 5:
#    sys.exit('please give 4 parameters. run: "python play_catpole.py <p1> <p2> <p3> <p4>"\n')


        # create task
        self.task = QuietDogTask(self.env)

        # create controller network
        # TODO: hmm, don't think we need a network.
        # figure out how to remove it
        # self.net = buildNetwork(4, 1, bias=False)

        # create agent and set parameters from command line
        # self.agent = DogAgent(self.net, None)
        # self.agent.module._setParameters(0.0, 0.0)

        # create experiment
        # self.experiment = EpisodicExperiment(task, self.agent)
        # self.experiment.doEpisodes(self.episodes)

        # run environment
        # ret = []
        # for n in range(self.agent.history.getNumSequences()):
        #     returns = self.agent.history.getSequence(n)
        #     reward = returns[2]
        #     ret.append(sum(reward, 0).item() )

        # print results
        # print(ret, "mean:",mean(ret))
        # env.getRenderer().stop()

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
        #pylab.gray()
        #pylab.ion()

        for i in range(1000):

            # interact with the environment (here in batch mode)
            self.experiment.doInteractions(100)
            self.agent.learn()
            self.agent.reset()

            # and draw the table
            #pylab.pcolor(self.table.params.reshape(2,5,4))
            #pylab.draw()

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
