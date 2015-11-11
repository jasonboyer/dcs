import base64
import boto3
from hub import constants
from hub.local.store import IStore
import pyaudio
import queue
import threading
import time


# Store to AWS Kinesis in raw format


class StoreFirehose(IStore):
    def __init__(self, audio_format, channels, rate, chunk, record_seconds, stream_name):
        super().__init__(audio_format, channels, rate, chunk, record_seconds)
        self.client = boto3.client('firehose')
        self.seq = 0
        self.chunks_per_put = int(record_seconds * rate / chunk)
        self.stream_name = stream_name
        # Queue to handle buffering of records
        # Sending records must be done in chunks to minimize network latency.
        # It also must be done off of the main thread, to avoid blocking the
        # audio recording loop, which is very real-time.
        # TODO: The queue size is limited only by memory, so it may grow large if there is a network outage
        self.records = queue.Queue()
        self.sender = FirehoseThread(self.records, self.chunks_per_put, self.client, self.stream_name)

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
        self.records.put_nowait({'Data': in_data})

    def stop_storing(self):
        super().stop_storing()
        # If non-daemon thread, should do cleanup here
        # self.sender.join(TERMINATE_TIMEOUT)


'''
 Thread to send data in batches to AWS Kinesis Firehose stream
 It needs to be done in a separate thread because the
 audio collection callback needs to run in real time to
 avoid dropping frames. The data is batched for efficiency
 and to stay within AWS Kinesis Firehose service limits for a
 single request.

'''


class FirehoseThread(threading.Thread):
    def __init__(self, records, records_per_put, client, stream_name):
        # Terminates without cleanup on program exit
        super().__init__(daemon=True)
        self.records = records
        self.records_per_put = records_per_put
        self.client = client
        self.stream_name = stream_name

    def run(self):
        self.call_run()

    def call_run(self):
        print('FirehoseThread starting')
        while True:
            records_to_send = []
            for i in range(self.records_per_put):
                # get records off the queue and append them to the list
                records_to_send.append(self.records.get())
            # Send the records in a group
            result_records = self.client.put_record_batch(
                DeliveryStreamName=self.stream_name,
                Records=records_to_send)
            print('Uploaded ' +
                  str(self.records_per_put - int(result_records['FailedPutCount'])) +
                  ' records (' +
                  str(result_records['FailedPutCount']) +
                  ' failed records)')
            if constants.VERBOSE:
                print('results_records: ' + str(result_records))

if __name__ == '__main__':
    # execute only if run as a script
    run_time = 3600*7
    test_hose = boto3.client('firehose')
    test_delivery_stream_name = 'audio_in'
    # Create a test stream, and wait for it to become active
#    test_hose.create_delivery_stream(DeliveryStreamName=test_delivery_stream_name,
#                                     S3DestinationConfiguration={
#                                         'RoleARN':'arn:aws:iam::814050614726:role/firehose_delivery_role',
#                                         'BucketARN':'arn:aws:s3:::boyer-cs767-audio'
#                                     }
#                                     )
    while True:
        status = test_hose.describe_delivery_stream(DeliveryStreamName=test_delivery_stream_name)
        if status['DeliveryStreamDescription']['DeliveryStreamStatus'] == 'ACTIVE':
            print('Stream ACTIVE: ' + test_delivery_stream_name)
            break
        time.sleep(1.0)

    # Run the test
    test_store = StoreFirehose(pyaudio.paFloat32, 1, constants.RATE, constants.SAMPLES_PER_RECORD, 1, test_delivery_stream_name)
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