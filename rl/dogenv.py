# Adapted from mazes.py from PyBrain

import boto.sqs
import boto.sqs.message
from boto.sqs.message import MHMessage
from hub import constants
import numpy
from pybrain.utilities import Named
from pybrain.rl.environments.simple import SimpleEnvironment
from random import random, choice
import re
import queue
from scipy import zeros
import threading
import time

# Setup sounds, volumes, and rewards/punishments
sounds = constants.SOUNDS
volume_levels = 4  # 0 = no sound, 3 = high volume
volume_rewards = [constants.REWARD_SOUND_NONE,
                  constants.REWARD_SOUND_LOW,
                  constants.REWARD_SOUND_MEDIUM,
                  constants.REWARD_SOUND_LOUD]
reward_tmp = numpy.array(range(2 * volume_levels * len(sounds))).reshape(2, volume_levels, len(sounds))
for x in range(volume_levels):
    reward_tmp[0][x].fill(volume_rewards[x]+constants.REWARD_DOG_QUIET)
    reward_tmp[1][x].fill(volume_rewards[x]+constants.REWARD_DOG_BARKING)
rewards = reward_tmp.reshape(2*volume_levels*len(sounds))

# Code adapted from http://stackoverflow.com/questions/4877624/numpy-array-of-objects
class ActionPlay:
    global sounds

    def __init__(self, volume_level, sound_index):

        self.sound_index = sound_index
        self.sound_file = sounds[self.sound_index]
        self.volume_level = volume_level

    def get_sound_index(self):
        return self.sound_index

    def get_sound_file(self):
        return self.sound_file

    def set_sound_file(self, sound_index):
        self.sound_file = sounds[sound_index]

    def get_volume_level(self):
        return self.volume_level

    def set_volume_level(self, volume_level):
        self.volume_level = volume_level

# Class to hold measured state about the outside world
class Sensors:
    def __init__(self):
        self.barking = 0
        self.sound = 0
        self.volume = 0

    # Convert the three environmental mesasurements into a single number representing the
    # current state. Think of two layers of blocks, with the bottom layer being
    # dog not barking (0) and the top layer being dog barking (1). Within a layer,
    # the row is selected by which sound is playing, and the column by the volume
    def asarray(self):
        return numpy.asarray([self.barking*len(sounds)*volume_levels+
                              self.sound*volume_levels+
                              self.volume])


class HubSender(threading.Thread):
    def __init__(self, hub_queue_name, source_queue):
        super().__init__()
        self.source_queue = source_queue
        self.conn = boto.sqs.connect_to_region(constants.REGION)
        self.hub_queue = self.conn.get_queue(hub_queue_name)
        self.hub_queue.set_message_class(MHMessage)

    def run(self):
        while True:
            action = self.source_queue.get(True)
            print('HubSender: sending message ' + action.get_sound_file() + ' ' + str(action.get_volume_level()))
            self.send_hub_message(action)

    def send_hub_message(self, action):
        cmess = MHMessage(self.hub_queue)
        cmess[constants.ATTR_COMMAND] = constants.PLAY_SOUND
        cmess[constants.ATTR_SOUND_FILE] = action.get_sound_file()
        cmess[constants.ATTR_VOLUME_LEVEL] = action.get_volume_level()
        self.hub_queue.write(cmess)


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

    all_actions = numpy.empty((len(sounds)*volume_levels), dtype=object)
    for i in range(volume_levels):
        for j in range(len(sounds)):
            all_actions[i*len(sounds)+j] = ActionPlay(i, j)

    # Target and starting point
    ALL_QUIET = 0

    # allStates = list(range(volume_levels))
    # DOG_QUIET = volume_levels
    # DOG_BARKING = DOG_QUIET + 1
    # allStates += [DOG_QUIET, DOG_BARKING]

    # stochasticity
    stochAction = 0
    stochObs = 0

    def __init__(self, goal_state, init_state, event_queue, hub_queue_name, **args):
        super().__init__()
        self.setArgs(**args)
        self.goal_state = goal_state
        self.init_state = init_state
        # Make sure boto has its own connection for this thread
        self.conn = boto.sqs.connect_to_region(constants.REGION)
        self.event_queue = event_queue
#        self.event_queue = self.conn.get_queue(event_queue_name)
#        self.event_queue.set_message_class(MHMessage)
        self.sensors = Sensors()
        self.source_queue = queue.Queue()
        self.hub_sender = HubSender(hub_queue_name, self.source_queue)
        self.hub_sender.start()

    def performAction(self, action):
        print('DogEnv.performAction() called')
        if self.stochAction > 0:
            if random() < self.stochAction:
                action = choice(list(range(len(self.all_actions))))
        action_play = self.all_actions[action]
        self.update(action_play)
        if action_play.get_volume_level() > 0 and action_play.get_sound_file() is not None:
            print('Putting sound message in Python queue: ' + action_play.get_sound_file() + ' ' + str(action_play.get_volume_level()))
            self.source_queue.put_nowait(action_play)

    def update(self, action_play):
        print('DogEnv.update() called')
        self.sensors.sound = action_play.get_sound_index()
        self.sensors.volume = action_play.get_volume_level()


    def getSensors(self):
        print('DogEnv.getSensors() called')
        messages = []
        while len(messages) < constants.RL_MESS_CHUNK:
            messages += self.event_queue.get_messages(constants.RL_MESS_CHUNK - len(messages))
        for message in messages:
            print('DogEnv: SQS message received: ' + str(message.get_body()))
            if message[constants.ATTR_DOG_STATE] == constants.DOG_STATE_BARKING:
                self.sensors.barking = 1
        return self.sensors.asarray()

    def f(self, state):
        global rewards
        ret = []
        for i in range(len(state)):
            ret.append(rewards[state])
        return ret

    def __str__(self):
        return ''

if __name__ == '__main__':
    conn = boto.sqs.connect_to_region(constants.REGION)
    p = re.compile('\.')
    test_queue_name = 'test_queue'.join(p.split(str(time.time())))
    hub_queue_name = 'hub_queue'.join(p.split(str(time.time())))
    dogenv = DogEnv(0, 0, test_queue_name)
    test_queue = conn.get_queue(test_queue_name)
    conn.delete_queue(test_queue)
    hub_queue = conn.get_queue(hub_queue_name)
    conn.delete_queue(hub_queue)
    print('Done')
