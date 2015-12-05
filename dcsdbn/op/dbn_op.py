''' Operating mode of Deep Belief Network
'''

import boto.kinesis
import boto.sqs
import boto.sqs.message as mess
import dbn.DBN
from hub import constants
from hub import feat_message
import numpy as np
import pickle
import threading
import time


class DbnOp(threading.Thread):
    def __init__(self, region, feature_queue_name,
                 command_queue_name, starting_point='LATEST', file=None):
        super.__init__()
        self.region = region
        self.feature_queue_name = feature_queue_name
        self.command_queue_name = command_queue_name
        self.starting_point = starting_point
        if file is None:
            self.file = 'pickled_test_fn.pck'
        else:
            self.file = file
        self.load_dbn()
        self.conn = boto.sqs.connect_to_region(constants.REGION)
        dcs_queues = self.conn.get_all_queues(prefix='dcs')
        if constants.VERBOSE:
            print(dcs_queues)
        if command_queue_name not in dcs_queues:
            print('Command queue is not set up')
            exit(-1)
        if feature_queue_name not in dcs_queues:
            print('Feature queue is not set up')
            exit(-1)
        self.command_queue = self.conn.get_queue(command_queue_name)
        self.feature_queue.set_message_type(boto.sqs.message.MHMessage)
        self.feature_queue = self.conn.get_queue(feature_queue_name)
        self.feature_queue.set_message_type(feat_message.FeatMessage)
        # Exponential probability distribution for testing
        self.dist = np.sort(np.random.exponential(0.17, 300))[::-1]
        # Probability of dog barking for testing
        self.initial_prob = 0.001

    def run(self):
        self.call_run()

    def call_run(self):
        while True:
            print('DBN Op Loop: ')
            mfcc_rec = []
            for i in range(constants.MFCCS_PER_RECORD):
                fmess = self.feature_queue.read()
                self.feature_queue.delete(fmess)
                if constants.VERBOSE:
                    print('dbn_op: received SQS message: ' + fmess)
                mfcc_rec.append(fmess.get_body())
            # Check current audio against learning model
            if self.dog_is_barking(mfcc_rec):
                self.send_hub_message(constants.DOG_STATE_BARKING)
            else:
                self.send_hub_message(constants.DOG_STATE_QUIET)

    def load_dbn(self, file):
        # load state from storage
        self.dbn = pickle.Unpickler.load(file)

    def dog_is_barking(self):
        # Use a random process to start barking
        # then use exponential decay to determine
        # whether the dog is still barking
        num = np.random.rand()
        self.episode_time -= 1
        if (self.episode_time > 0):
            if (num < self.dist[self.episode_time]):
                return True
        else:
            if (num < self.initial_prob):
                self.episode_time = constants.EPISODE_TIME
                return True
        return False

    def send_hub_message(self, state):
        cmess = boto.sqs.message.MHMessage()
        cmess[constants.ATTR_DOG_STATE] = state
        self.command_queue.write(cmess)
