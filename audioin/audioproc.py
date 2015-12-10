''' Reads sound samples from an AWS Kinesis stream and converts to
    MFCCs. Uses https://github.com/jameslyons/python_speech_features
    to calculate the MFCCs.

    Sends the MFCCs to an output queue.
'''

import time
import base64
import boto.kinesis
from features import mfcc
from features import logfbank
from hub import constants
from hub.feat_message import FeatMessage
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import queue
import threading

VERBOSE = False
REGION = 'us-east-1'
FFTSIZE = 512
FFTKEEPSIZE = 257


class AudioProc(threading.Thread):
    def __init__(self, input_stream_name, output_queue_name, rate, samples_per_record,
                 chunk, step, starting_point='LATEST'):
        super().__init__()
        self.input_stream = input_stream_name
        self.rate = rate
        self.samples_per_record = int(samples_per_record)
        self.chunk = int(chunk)
        self.step = int(step)
        # starting_point can be 'LATEST' to start processing the most recent
        # records, or 'TRIM_HORIZON' to start processing the oldest records
        self.starting_point = starting_point
        self.sample_spacing = 1/rate
        self.fft_size = FFTSIZE
        self.fft_keep_size = FFTKEEPSIZE
        self.region = REGION
        #if VERBOSE:
        print('Kinesis regions: ' + str(boto.kinesis.regions()))
        self.kin = boto.kinesis.connect_to_region(self.region)
        #if VERBOSE:
        print('Available streams: ' + str(self.kin.list_streams()))
        self.limit = 100
        # Make sure boto has its own connection for this thread
        self.conn = boto.sqs.connect_to_region(self.region)
        self.output_queue = self.conn.get_queue(output_queue_name)
        self.output_queue.set_message_class(FeatMessage)

    def run(self):
        # For unit testing, have a separate function body
        self.call_run()

    def call_run(self):
        print('audioproc: self.input_stream: ' + self.input_stream)
        status = self.kin.describe_stream(self.input_stream)
        if status['StreamDescription']['StreamStatus'] == 'ACTIVE':
            print('Stream is available: ' + self.input_stream)

        # could also use Kinesis stream
        #print('audioproc: self.output_queue: ' + self.output_queue)
        #status = self.kin.describe_stream(self.output_queue)
        #if status['StreamDescription']['StreamStatus'] == 'ACTIVE':
        #    print('Stream is available: ' + self.output_stream)

        # TODO: catch boto.kinesis.exceptions.ExpiredIteratorException:
        # ExpiredIteratorException: 400 Bad Request
        # {'__type': 'ExpiredIteratorException', 'message':
        # 'Iterator expired. The iterator was created at time
        # Thu Dec 10 01:59:39 UTC 2015 while right now it is
        # Thu Dec 10 02:06:15 UTC 2015 which is further in the
        # future than the tolerated delay of 300000 milliseconds.'}

        shardit = self.kin.get_shard_iterator(self.input_stream,
                                              status['StreamDescription']['Shards'][0]['ShardId'],
                                              self.starting_point)['ShardIterator']
        while True:
            record_batch = self.kin.get_records(shardit, self.limit, False)
            shardit = record_batch['NextShardIterator']
            if len(record_batch['Records']) == 0:
                # Don't call get_records in a tight loop when there is no data yet
                # This avoids exceeding the AWS API limit of 5 calls per second
                time.sleep(0.2)
                continue
            # Each record is chunk samples.
            # Convert back to an array of floats
            print('processing ' + str(len(record_batch['Records'])) + 'records')
            in_bytes = b'' # bytearray() # np.array('', np.bytes_)
            for rec in record_batch['Records']:
                batch_bytes = base64.b64decode(rec['Data'])
                in_bytes += batch_bytes

            # Convert byte array to sample array
            if len(in_bytes) > 0: # = self.samples_per_record:
                my_y = np.fromstring(in_bytes, np.float32)

            # Loop by step intervals, using a frame size of chunk samples
            for sample in range(0, int((len(my_y) - self.chunk)/self.step)):
                my_y_subset = my_y[sample*self.step:sample*self.step+self.chunk-1:1]

                # Do the math
                mfcc_feat = mfcc(my_y_subset, self.rate)
                #fbank_feat = logfbank(my_y_subset, self.rate)

                # Send the features out to anyone who is listening
                mess = FeatMessage(body=mfcc_feat, queue=self.output_queue)
                self.output_queue.write(mess)

if __name__ == '__main__':
    # execute only if run as a script
    # 'test_stream1446121778.355943'
    input_stream = 'data_stream1449633467.770991'
    output_queue_name = '1449633537feature_queue784543'
    conn = boto.sqs.connect_to_region(constants.REGION)
    output_queue = conn.get_queue(output_queue_name)

    proc = AudioProc(input_stream, output_queue, 96000, 96000/100, 96000/40, 96000/100,
                     'TRIM_HORIZON')
    proc.call_run()

    # output_queue should have MFCCs
    while True:
        features = output_queue.read()
        print(features)
