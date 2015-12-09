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
        super().__init__()
        self.region = region
        self.starting_point = starting_point
        if file is None:
            self.file = 'pickled_test_fn.pck'
        else:
            self.file = file
        self.dbn = None
        self.load_dbn(self.file)
        # Make sure boto has its own connection for this thread
        self.conn = boto.sqs.connect_to_region(self.region)
        dcs_queues = [q.name for q in self.conn.get_all_queues(prefix='dcs')]
        #if constants.VERBOSE:
        print('Available dcs_queues: ' + str(dcs_queues))

        if command_queue_name not in dcs_queues:
            print('Command queue ' + command_queue_name + ' is not set up')
            exit(-1)
        self.command_queue = self.conn.get_queue(command_queue_name)
        self.command_queue.set_message_class(boto.sqs.message.MHMessage)

        self.feature_queue = self.conn.get_queue(feature_queue_name)
        if self.feature_queue is None:
            print('Feature queue ' + feature_queue_name + ' is not set up')
            exit(-1)
        self.feature_queue.set_message_class(feat_message.FeatMessage)

        # Exponential probability distribution for testing
        self.dist = np.sort(np.random.exponential(0.17, 300))
        # Probability of dog barking for testing
        self.initial_prob = 0.02
        self.episode_time = 0

    def run(self):
        self.call_run()

    def call_run(self):
        while True:
            print('DBN Op Loop: ')
            mfcc_rec = []
            for i in range(constants.MFCCS_PER_RECORD):
                fmess = self.feature_queue.read(visibility_timeout=None,
                                                wait_time_seconds=1)
                if fmess is None:
                    continue
                self.feature_queue.delete_message(fmess)
                if constants.VERBOSE:
                    print('dbn_op: received SQS message: ' + fmess)
                mfcc_rec.append(fmess.get_body())
            # Check current audio against learning model
            if self.dog_is_barking(mfcc_rec):
                self.send_hub_message(constants.DOG_STATE_BARKING)
            else:
                self.send_hub_message(constants.DOG_STATE_QUIET)

    def load_dbn(self, file):
        # TODO: load state from storage
        # self.dbn = pickle.Unpickler(file).load()
        pass

    def dog_is_barking(self, mfcc_rec):
        # Use a random process to start barking
        # then use exponential decay to determine
        # whether the dog is still barking
        # TODO: This should be passing the mfcc_rec into the trained DBN
        if constants.VERBOSE:
            print(mfcc_rec)
        num = np.random.rand()
        self.episode_time -= 1
        if self.episode_time > 0:
            if num < self.dist[self.episode_time]:
                return True
        else:
            if num < self.initial_prob:
                # Start a new barking episode
                print('Starting a new barking episode')
                self.episode_time = constants.EPISODE_TIME
                return True
        return False

    def send_hub_message(self, state):
        cmess = boto.sqs.message.MHMessage(self.command_queue)
        cmess[constants.ATTR_COMMAND] = constants.ATTR_DOG_STATE
        cmess[constants.ATTR_DOG_STATE] = state
        self.command_queue.write(cmess)
