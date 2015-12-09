''' Hub program that runs on an AWS EC2 instance. Its responsibilities are:
    - Listen for messages on the SQS hub queue
    - Bring up EC2 instances as needed
    - Dispatch instructions to other remote modules
    - Dispatch instructions to local hub
'''

from audioin.audioproc import AudioProc
import boto.kinesis
import boto.sqs
import boto.sqs.message as mess
import boto3
from dcsdbn.op import dbn_op
from rl import rl_op
from hub import constants
import queue
import re
import time


class RemoteHub:
    def __init__(self):
        self.kin = boto.kinesis.connect_to_region(constants.REGION)
        self.conn = boto.sqs.connect_to_region(constants.REGION)
        self.audio_proc = None
        self.dbn_op = None
        self.rl_op = None
        self.hub_queue_name = constants.HUB_QUEUE_UP
        self.hub_queue_down_name = constants.HUB_QUEUE_DOWN
        self.event_queue_name = constants.EVENT_QUEUE

        dcs_queues = self.conn.get_all_queues(prefix='dcs')
        if constants.VERBOSE:
            print(dcs_queues)
        queue_names = [q.name for q in dcs_queues]

        if self.hub_queue_name not in queue_names:
            # setup_dcs.setup_dcs()
            print('Hub up queue is not set up')
            exit(-1)
        if self.hub_queue_down_name not in queue_names:
            # setup_dcs.setup_dcs()
            print('Hub down queue is not set up')
            exit(-1)
        if self.event_queue_name not in queue_names:
            # setup_dcs.setup_dcs()
            print('Event queue is not set up')
            exit(-1)
        self.hub_queue = self.conn.get_queue(self.hub_queue_name)
        self.hub_queue.set_message_class(mess.MHMessage)
        self.hub_queue_down = self.conn.get_queue(self.hub_queue_down_name)
        self.hub_queue_down.set_message_class(mess.MHMessage)
        self.event_queue = self.conn.get_queue(self.event_queue_name)
        self.event_queue.set_message_class(mess.MHMessage)
        p = re.compile('\.')
        self.feature_queue_name = 'dcs_' + 'feature_queue'.join(p.split(str(time.time())))
        self.feature_queue = self.conn.create_queue(self.feature_queue_name)
        # Wait for feature queue to be ready
        while True:
            if self.conn.lookup(self.feature_queue_name):
                break;
            time.sleep(1.0)

    def run(self):
        while True:
            m = self.hub_queue.read(visibility_timeout=None,
                                    wait_time_seconds=1)
            if m is None:
                continue
            self.hub_queue.delete_message(m)
            # m = mess.MHMessage(raw_mess.get_body())
            # if constants.VERBOSE:
            print('hub_remote: received SQS message: ' + str(m.get_body()))
            command = m[constants.ATTR_COMMAND]
            if command == constants.START_OPERATING:
                self.do_start(m[constants.ATTR_STREAM_NAME])
            elif command == constants.STOP_OPERATING:
                self.do_stop()
            elif command == constants.ATTR_DOG_STATE:
                self.report_barking_state(m)
            elif command == constants.PLAY_SOUND:
                print('hub_remote: outputting sound: ' + str(m.get_body()))
                self.output_sound(m[constants.ATTR_SOUND_FILE],
                                  m[constants.ATTR_VOLUME_LEVEL])

    def do_start(self, data_stream_name):
        print('Called do_start()')

        ''' TODO: use a feature stream or SQS queue
        # Create a feature stream, and wait for it to become active
        self.kin.create_stream(self.feature_stream_name, 1)
        while True:
            status = self.kin.describe_stream(self.feature_stream_name)
            if status['StreamDescription']['StreamStatus'] == 'ACTIVE':
                print('Stream is ACTIVE: ' + self.feature_stream_name)
                break
            time.sleep(1.0)
        '''

        # Create and dispatch an AudioProc, which will listen to the data stream
        # and produce features on the feature queue
        print('Create AudioProc(' + data_stream_name + ')')
        self.audio_proc = AudioProc(data_stream_name, self.feature_queue_name, constants.RATE,
                                    constants.SAMPLES_PER_RECORD, constants.CHUNK,
                                    constants.STEP, 'TRIM_HORIZON')
        self.audio_proc.start()

        # Create and dispatch a DBN operational module, which will determine whether
        # the dog is barking, based on the feature stream
        self.dbn_op = dbn_op.DbnOp(constants.REGION, self.feature_queue_name, self.hub_queue_name)
        self.dbn_op.start()

        # Create and dispatch a RL operational module, which will determine which
        # sounds at what volume to play. Based on whether the dog stops barking, and
        # the unpleasantness of the sounds, it will learn which sounds work best.
        # the RL module reads dog status messages from the event_queue and writes
        # play sound commands to the hub_queue
        self.rl_op = rl_op.RlOp(self.event_queue_name, self.hub_queue_name)
        self.rl_op.start()


    # Delete expensive resources before exiting.
    # Give other components a chance to save state.
    # Stop in reverse order of starting.
    def do_stop(self):
        print('Called do_stop()')
        self.dbn_op.stop()
        self.audio_proc.stop()
        #self.kin.delete_stream(self.feature_stream_name, 1)

    # Tell the reinforcement learning module the current barking state
    def report_barking_state(self, state_mess):
        m = mess.MHMessage(self.event_queue, state_mess)
        self.event_queue.write(m)

    # Tell the local hub to play a sound at a volume
    def output_sound(self, sound_file, volume_level):
        m = mess.MHMessage(self.hub_queue_down)
        m[constants.ATTR_COMMAND] = constants.PLAY_SOUND
        m[constants.ATTR_SOUND_FILE] = sound_file
        m[constants.ATTR_VOLUME_LEVEL] = str(volume_level)
        self.hub_queue_down.write(m)


if __name__ == '__main__':
    hub = RemoteHub()
    hub.run()
    time.sleep(3600*7)



