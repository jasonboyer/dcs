import numpy as np
from pybrain.rl.environments.simple import MinimizeTask
from pybrain.rl.environments.task import Task
from random import random, choice



# Adapted from http://pybrain.org/docs/tutorial/reinforcement-learning.html

class QuietDogTask(MinimizeTask):
    def __init__(self, env):
        super().__init__(env)
        self.env = env

    def performAction(self, action):
        """ The action vector is stripped and the only element is cast to integer and given
            to the super class.
        """
        Task.performAction(self, int(action[0]))

    def getReward(self):
        # sleep(0.01)
        # print(self.state, self.action)
        reward = self.env.f([s for s in self.state])
        return - sum(reward)
