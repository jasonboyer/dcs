# Adapted from mazes.py from PyBrain

import boto.sqs
import boto.sqs.message
from hub import constants
import numpy
from pybrain.utilities import Named
from pybrain.rl.environments.simple import SimpleEnvironment
from random import random, choice
import re
from scipy import zeros
import time

sounds = [None, 'thunder.wav', 'enh.wav', 'no.wav', 'rustycrate.wav']
volume_levels = 4  # 0 = no sound, 3 = high volume

# Code adapted from http://stackoverflow.com/questions/4877624/numpy-array-of-objects
class ActionPlay:
    global sounds

    def __init__(self, sound_index, volume_level):
        self.sound_file = sounds[sound_index]
        self.volume_level = volume_level

    def get_sound_file(self):
        return sounds[self.sound_index]

    def set_sound_file(self, sound_index):
        self.sound_file = sounds[sound_index]

    def get_volume_level(self):
        return self.volume_level

    def set_volume_level(self, volume_level):
        self.volume_level = volume_level

# Class to hold measured state about the outside world
class Sensors:
    def __init__(self):
        self.barking = 0.0
        self.sound = 0.0
        self.volume = 0.0

    def asarray(self):
        return [self.barking]

class DogEnv(SimpleEnvironment, Named):
    """ Dog Environment, with actions being the the playing of
    sounds.
    The starting state is dog not barking, which is also the goal state.
    An episode begins when the dog is barking state is reached, by external
    feedback. Once the dog is barking, an action is taken, either play a sound
    or not play a sound, and play it at high or low volume. The number of actions
    is the number of sounds multiplied by the number of volume levels, plus the
    action of no sound. An action lasts as long as the sound clip being played,
    or n seconds of silence.

    The reward is determined by whether the dog stopped barking in the n seconds
    after the action was taken. The reward is divided by the volume level of
    the sound, because lower volumes are more desirable.

    """

    # table of booleans
    mazeTable = None

    # single goal
    goal = None

    # list of possible initial states
    initPos = None

    # Initialize the actions array
    v_actions = numpy.vectorize(ActionPlay)

    init_row = numpy.arange(len(sounds))
    init_col = numpy.arange(volume_levels)
#    init_arry = numpy.arange(len(sounds) * volume_levels).\
#        reshape((len(sounds), volume_levels))

    allActions = numpy.empty((len(sounds), volume_levels), dtype=object)
    for i in range(len(sounds)):
        for j in range(volume_levels):
            allActions[i, j] = ActionPlay(i, j)

    allStates = list(range(volume_levels))
    DOG_QUIET = volume_levels
    DOG_BARKING = DOG_QUIET + 1
    allStates += [DOG_QUIET, DOG_BARKING]

    # stochasticity
    stochAction = 0.
    stochObs = 0.

    def __init__(self, goal_state, init_state, event_queue, **args):
        self.setArgs(**args)
        self.goal_state = goal_state
        self.init_state = init_state
        self.event_queue = event_queue
        self.sensors = Sensors()

    def performAction(self, action):
        print('DogEnv.performAction() called')
        if self.stochAction > 0:
            if random() < self.stochAction:
                action_sound_index = choice(list(range(self.allActions.shape[0])))
                action_volume = choice(list(range(self.allActions.shape[1])))
                action = self.allActions[action_sound_index, action_volume]
        if action.get_volume_level() > 0 and action.get_sound_file() is not None:
            self.send_hub_message(action)

    def update(self):
        print('DogEnv.update() called')


    def getSensors(self):
        print('DogEnv.getSensors() called')
        messages = self.event_queue.get_messages()
        for message in messages:
            if message[constants.ATTR_DOG_STATE] == constants.DOG_STATE_BARKING:
                self.sensors.barking = 1.0

    def send_hub_message(self, action):
        cmess = boto.sqs.message.MHMessage()
        cmess[constants.ATTR_COMMAND] = constants.PLAY_SOUND
        cmess[constants.ATTR_SOUND_FILE] = action.get_sound_file()
        cmess[constants.ATTR_VOLUME_LEVEL] = action.get_volume_level()
        self.event_queue.write(cmess)

    def __str__(self):
        return ''

if __name__ == '__main__':
    conn = boto.sqs.connect_to_region(constants.REGION)
    p = re.compile('\.')
    test_queue = conn.create_queue('test_queue'.join(p.split(str(time.time()))))
    dogenv = DogEnv(0, 0, test_queue)
    conn.delete_queue(test_queue)
    print('Done')
