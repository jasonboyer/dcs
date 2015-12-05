import numpy as np

# Adapted from http://pybrain.org/docs/tutorial/reinforcement-learning.html

class QuietDogTask(MinimizeTask):
    def __init__(self, env):
        self.env = env

    def performAction(self, action):
        if self.stochAction > 0:
            if np.random.rand() < self.stochAction:
                action_sound_index = choice(list(range(self.allActions.shape[0])))
                action_volume = choice(list(range(self.allActions.shape[1])))
                action = self.allActions[action_sound_index, action_volume]
