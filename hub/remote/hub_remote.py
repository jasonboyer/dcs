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
from dcsdbn.op import dbn_op
from hub import constants
import time


class RemoteHub:
    def __init__(self):
        self.kin = boto.kinesis.connect_to_region(constants.REGION)
        self.conn = boto.sqs.connect_to_region(constants.REGION)
        self.audio_proc = None
        dcs_queues = self.conn.get_all_queues(prefix='dcs')
        if constants.VERBOSE:
            print(dcs_queues)
        if constants.HUB_QUEUE not in dcs_queues:
            # setup_dcs.setup_dcs()
            print('Hub queue is not set up')
            exit(-1)
        self.hub_queue = self.conn.get_queue(constants.HUB_QUEUE_UP)
        self.hub_queue_down = self.conn.get_queue(constants.HUB_QUEUE_DOWN)
        self.episode_time = 0

    def run(self):
        while True:
            raw_mess = self.hub_queue.read()
            self.hub_queue.delete(raw_mess)
            m = mess.MHMessage(raw_mess.get_body())
            if constants.VERBOSE:
                print('hub_remote: received SQS message: ' + m)
            command = m[constants.ATTR_COMMAND]
            if command == constants.START_OPERATING:
                self.do_start(m[constants.ATTR_STREAM_NAME])
            elif command == constants.STOP_OPERATING:
                self.do_stop()
            elif command == constants.ATTR_DOG_STATE:
                self.report_barking_state()
            elif command == constants.PLAY_SOUND:
                self.output_sound(m[constants.ATTR_SOUND_FILE],
                                  m[constants.ATTR_VOLUME_LEVEL])

    def do_start(self, data_stream_name):
        print('Called do_start()')
        feature_stream_name = 'feature_stream' + str(time.time())
        # Create a feature stream, and wait for it to become active
        self.kin.create_stream(feature_stream_name, 1)
        while True:
            status = self.kin.describe_stream(feature_stream_name)
            if status['StreamDescription']['StreamStatus'] == 'ACTIVE':
                print('Created stream: ' + feature_stream_name)
                break
            time.sleep(1.0)
        # Create and dispatch an AudioProc, which will listen to the data stream
        # and produce features on the feature stream
        self.audio_proc = AudioProc(data_stream_name, feature_stream_name, constants.RATE,
                                    constants.SAMPLES_PER_RECORD, constants.CHUNK,
                                    constants.STEP, 'TRIM_HORIZON')
        self.dbn_op = dbn_op.DbnOp(constants.REGION, feature_stream_name, self.hub_queue)

    def do_stop(self):
        print('Called do_stop()')

    def report_barking_state(self):
        if (self.episode_time > 0):
            self.episode_time -= 1

    def output_sound(self, sound_file, volume_level):
        m = mess.MHMessage(hub_queue_down)





