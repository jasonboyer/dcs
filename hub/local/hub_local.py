''' Runs the DCS.
    Communicates via SQS to the remote hub.
    Starts and stops local modules and dispatches messages to them.
'''

from audioout.audio_out import AudioOut
import boto.kinesis
import boto.sqs
from boto.sqs.message import MHMessage
import boto3
from hub import constants
from hub.local import store_kinesis, store_firehose
import pyaudio
import threading
import time


class LocalHub(threading.Thread):
    def __init__(self, store_type):
        super().__init__()
        self.store_type = store_type
        self.store = None
        self.stream_name = None
        self.audio_out = None
        conn = boto.sqs.connect_to_region(constants.REGION)
        dcs_queues = conn.get_all_queues(prefix='dcs')
        if constants.VERBOSE:
            print(dcs_queues)
        queue_names = [q.name for q in dcs_queues]
        if constants.HUB_QUEUE_UP not in queue_names:
            print('Up queue does not exist.')
            exit(-1)
        self.hub_queue_up = conn.get_queue(constants.HUB_QUEUE_UP)
        self.hub_queue_up.set_message_class(MHMessage)
        self.hub_queue_up.purge()
        if constants.HUB_QUEUE_DOWN not in queue_names:
            print('Down queue does not exist.')
            exit(-1)
        self.hub_queue_down = conn.get_queue(constants.HUB_QUEUE_DOWN)
        self.hub_queue_down.set_message_class(MHMessage)
        self.hub_queue_down.purge()

    def run(self):
        self.call_run()

    def call_run(self):
        if self.store_type == store_kinesis.StoreKinesis:
            self.run_kinesis()
        elif self.store_type == store_firehose.StoreFirehose:
            self.run_firehose()
        else:
            print('Unsupported store type: ' + str(self.store_type))
        self.store.start_storing()
        self.store.start()

        # Start the remote hub
        # TODO: run boto commands to spawn an EC2 instance that
        # runs the remote hub
        m = MHMessage(self.hub_queue_up)
        m[constants.ATTR_COMMAND] = constants.START_OPERATING
        m[constants.ATTR_STREAM_NAME] = self.stream_name
        self.hub_queue_up.write(m)

        # Message loop
        while True:
            m = self.hub_queue_down.read(visibility_timeout=None,
                                         wait_time_seconds=1)
            if m is None:
                continue
            self.hub_queue_down.delete_message(m)
            # m = MHMessage(raw_mess.get_body())
            #if constants.VERBOSE:
            print('hub_remote: received SQS message: ' + str(m.get_body()))
            command = m[constants.ATTR_COMMAND]
            if command == constants.PLAY_SOUND:
                audio_out = AudioOut(m[constants.ATTR_SOUND_FILE],
                                     m[constants.ATTR_VOLUME_LEVEL])
                audio_out.play()

    def stop(self):
        m = MHMessage(self.hub_queue_up)
        m[constants.ATTR_COMMAND] = constants.STOP_OPERATING
        self.hub_queue_up.write(m)
        self.store.stop_storing()
        self.store.stop()

    def run_kinesis(self):
        self.stream_name = 'data_stream' + str(time.time())
        # Create a data stream, and wait for it to become active
        kin = boto.kinesis.connect_to_region(constants.REGION)
        kin.create_stream(self.stream_name, 1)
        while True:
            print('Waiting for Kinesis stream ' +
                  self.stream_name + ' to become ACTIVE')
            status = kin.describe_stream(self.stream_name)
            if status['StreamDescription']['StreamStatus'] == 'ACTIVE':
                print('Created stream: ' + self.stream_name)
                break
            time.sleep(1.0)

        self.store = store_kinesis.StoreKinesis(pyaudio.paFloat32, 1, constants.RATE,
                                           constants.SAMPLES_PER_RECORD, 1,
                                           self.stream_name)

    def run_firehose(self):
        hose = boto3.client('firehose')
        self.stream_name = 'audio_in'
        # Create a stream, and wait for it to become active
    #    hose.create_delivery_stream(DeliveryStreamName=test_delivery_stream_name,
    #                                     S3DestinationConfiguration={
    #                                         'RoleARN':'arn:aws:iam::814050614726:role/firehose_delivery_role',
    #                                         'BucketARN':'arn:aws:s3:::boyer-cs767-audio'
    #                                     }
    #                                     )
        while True:
            print('Waiting for Kinesis Firehose stream ' +
                  self.stream_name + ' to become ACTIVE')
            status = hose.describe_delivery_stream(DeliveryStreamName=self.stream_name)
            if status['DeliveryStreamDescription']['DeliveryStreamStatus'] == 'ACTIVE':
                print('Stream ACTIVE: ' + self.stream_name)
                break
            time.sleep(1.0)

        # Start recording audio
        self.store = store_firehose.StoreFirehose(pyaudio.paFloat32, 1, constants.RATE, constants.SAMPLES_PER_RECORD, 1, self.stream_name)

if __name__ == '__main__':
    # execute only if run as a script
    run_time = 3600*7
    hub = LocalHub(store_kinesis.StoreKinesis)
    hub.start()
    time.sleep(run_time)
    hub.stop()