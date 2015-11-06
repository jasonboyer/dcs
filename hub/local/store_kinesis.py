import base64
import boto.kinesis
from hub import constants
from hub.local.store import IStore
import pyaudio
import queue
import threading
import time


# Store to AWS Kinesis in raw format


class StoreKinesis(IStore):
    def __init__(self, audio_format, channels, rate, chunk, record_seconds, stream_name):
        super().__init__(audio_format, channels, rate, chunk, record_seconds)
        self.seq = 0
        self.chunks_per_put = int(record_seconds * rate / chunk)
        # setup Amazon Kinesis upload
        self.region = constants.REGION
        self.stream_name = stream_name
        if constants.VERBOSE:
            print('Kinesis regions: ' + str(boto.kinesis.regions()))
        self.kin = boto.kinesis.connect_to_region(self.region)
        if constants.VERBOSE:
            print('Available streams: ' + str(self.kin.list_streams()))
        # Queue to handle buffering of records
        # Sending records must be done in chunks to minimize network latency.
        # It also must be done off of the main thread, to avoid blocking the
        # audio recording loop, which is very real-time.
        # TODO: The queue size is limited only by memory, so it may grow large if there is a network outage
        self.records = queue.Queue()
        self.sender = KinesisThread(self.records, self.chunks_per_put, self.kin, self.stream_name)

    def start(self):
        self.sender.start()

    def run(self):
        self.sender.call_run()

    # Callback with chunk audio samples in in_data

    def store_data(self, in_data):
        if constants.VERBOSE:
            print('store_data(): qsize(records): ' + str(self.records.qsize()))
        # each record is n chunks of audio samples, base64 encoded
        # TODO: catch Full exception
        self.records.put_nowait({'Data': base64.b64encode(in_data).decode('utf-8'),
                                'PartitionKey': '1'})

    def stop_storing(self):
        super().stop_storing()
        # If non-daemon thread, should do cleanup here
        # self.sender.join(TERMINATE_TIMEOUT)


'''
 Thread to send data in batches to AWS Kinesis stream
 It needs to be done in a separate thread because the
 audio collection callback needs to run in real time to
 avoid dropping frames. The data is batched for efficiency
 and to stay within AWS Kinesis service limits for a single
 shard.

'''


class KinesisThread(threading.Thread):
    def __init__(self, records, records_per_put, kin, stream_name):
        # Terminates without cleanup on program exit
        super().__init__(daemon=True)
        self.records = records
        self.records_per_put = records_per_put
        self.kin = kin
        self.stream_name = stream_name

    def run(self):
        self.call_run()

    def call_run(self):
        print('KinesisThread starting')
        while True:
            records_to_send = []
            for i in range(self.records_per_put):
                # get records off the queue and append them to the list
                records_to_send.append(self.records.get())
            # Send the records in a group
            result_records = self.kin.put_records(records_to_send,
                                                  stream_name=self.stream_name,
                                                  b64_encode=False
                                                  )
            print('Uploaded ' +
                  str(self.records_per_put - int(result_records['FailedRecordCount'])) +
                  ' records (' +
                  str(result_records['FailedRecordCount']) +
                  ' failed records)')
            if constants.VERBOSE:
                print('results_records: ' + str(result_records))

if __name__ == '__main__':
    # execute only if run as a script
    run_time = 20  # 3600*3.5
    test_kin = boto.kinesis.connect_to_region(constants.REGION)
    test_stream_name = 'test_stream' + str(time.time())
    # Create a test stream, and wait for it to become active
    test_kin.create_stream(test_stream_name, 1)
    while True:
        status = test_kin.describe_stream(test_stream_name)
        if status['StreamDescription']['StreamStatus'] == 'ACTIVE':
            print('Created stream: ' + test_stream_name)
            break
        time.sleep(1.0)

    # Run the test
    test_store = StoreKinesis(pyaudio.paFloat32, 1, constants.RATE, constants.SAMPLES_PER_RECORD, 1, test_stream_name)
    test_store.start_storing()
    test_store.run()
    time.sleep(run_time)
    test_store.stop_storing()

'''
    # Read the records back
    # Approximate number of records to read
    time.sleep(5)
    records_to_read = (run_time - 1) * RATE / CHUNK
    status = test_kin.describe_stream(test_stream_name)
    shard_id = status['StreamDescription']['Shards'][0]['ShardId']
    shard_it = test_kin.get_shard_iterator(test_stream_name, shard_id, 'TRIM_HORIZON')['ShardIterator']
    num_records_down = 0
    while True:
        test_records = test_kin.get_records(shard_it, 100, False)
        print(test_records.keys())
        print('Downloaded ' + str(len(test_records['Records'])) + ' records')
        num_records_down += len(test_records['Records'])
        if num_records_down >= records_to_read or (num_records_down > 0 and len(test_records['Records']) == 0):
            break
        shard_it = test_records['NextShardIterator']
        time.sleep(1.0)
    print('Deleting stream ' + test_stream_name)
    test_kin.delete_stream(test_stream_name)
'''