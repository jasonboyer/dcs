''' Operating mode of Deep Belief Network
'''

import boto.kinesis
from hub import constants
import threading
import time


class DbnOp(threading.Thread):
    def __init__(self, region, state_url, data_thread_name, command_queue_name):
        super.__init__()
        self.region = region
        self.state_url = state_url
        self.data_thread_name = data_thread_name
        self.command_queue_name = command_queue_name
        if constants.VERBOSE:
            print('Kinesis regions: ' + str(boto.kinesis.regions()))
        self.kin = boto.kinesis.connect_to_region(region)
        if constants.VERBOSE:
            print('Available streams: ' + str(self.kin.list_streams()))
        self.dbn = self.read_state()

    def run(self):
        while True:
            print('DBN Op Loop: ')
            time.sleep(10)
