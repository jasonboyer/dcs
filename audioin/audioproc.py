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
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import queue
import threading

VERBOSE = False
REGION = 'us-east-1'
FFTSIZE = 512
FFTKEEPSIZE = 257


class AudioProc(threading.Thread):
    def __init__(self, input_stream, output_stream, rate, samples_per_record,
                 chunk, step, starting_point='LATEST'):
        super().__init__()
        self.input_stream = input_stream
        self.output_stream = output_stream
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
        if VERBOSE:
            print('Kinesis regions: ' + str(boto.kinesis.regions()))
        self.kin = boto.kinesis.connect_to_region(self.region)
        if VERBOSE:
            print('Available streams: ' + str(self.kin.list_streams()))
        self.limit = 100

    def run(self):
        # For unit testing, have a separate function body
        self.call_run()

    def call_run(self):
        status = self.kin.describe_stream(self.input_stream)
        if status['StreamDescription']['StreamStatus'] == 'ACTIVE':
            print('Stream is available: ' + self.input_stream)
        status = self.kin.describe_stream(self.output_stream)
        if status['StreamDescription']['StreamStatus'] == 'ACTIVE':
            print('Stream is available: ' + self.output_stream)
        shit = self.kin.get_shard_iterator(self.input_stream,
                                           status['StreamDescription']['Shards'][0]['ShardId'],
                                           self.starting_point)['ShardIterator']
        while True:
            record_batch = self.kin.get_records(shit, self.limit, False)
            shit = record_batch['NextShardIterator']
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
                my_foo_wtf = base64.b64decode(rec['Data'])
                in_bytes += my_foo_wtf

            # Convert byte array to sample array
            if len(in_bytes) > 0: # = self.samples_per_record:
                my_y = np.fromstring(in_bytes, np.float32)

            # Loop by step intervals, using a frame size of chunk samples
            for sample in range(0, int((len(my_y) - self.chunk)/self.step)):
                my_y_subset = my_y[sample*self.step:sample*self.step+self.chunk-1:1]

                # Do the math
                mfcc_feat = mfcc(my_y_subset, self.rate)
                fbank_feat = logfbank(my_y_subset, self.rate)

                # Send the features out to anyone who is listening
                self.output_queue.put_nowait(mfcc_feat)

if __name__ == '__main__':
    # execute only if run as a script
    # 'test_stream1446121778.355943'
    input_stream = 'test_stream1446310304.28351'
    output_stream = 'dcs_feature_stream'
    proc = AudioProc(input_stream, output_stream, 96000, 96000/100, 96000/40, 96000/100,
                     'TRIM_HORIZON')
    proc.call_run()

    # output_queue should have MFCCs
    while True:
        features = output_queue.get(True)
        print(features)
