''' Reconstructs sound samples from a Kinesis Firehose blob
'''

import time
import base64
import boto.s3
import boto.s3.connection
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import pyaudio
import queue
import threading
from features import mfcc
from features import logfbank

VERBOSE = False
DEBUG = False
REGION = 'us-east-1'
FFTSIZE = 512
FFTKEEPSIZE = 257


class ChunksFromS3:
    def __init__(self, bucket_name, year, month, day, hour, rate, samples_per_record,
                 chunk, step, minute=0, output_queue=None):
        self.bucket_name = bucket_name
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.rate = rate
        self.samples_per_record = int(samples_per_record)
        self.chunk = int(chunk)
        self.step = int(step)
        self.minute = minute
        self.output_queue = output_queue
        self.sample_spacing = 1/rate
        self.region = REGION
        if VERBOSE:
            print("Available S3 regions: ")
            print(boto.s3.regions())
        self.limit = 100

    def play_blob(self, minute=None):
        if minute is None:
            minute = self.minute
        conn = boto.s3.connection.S3Connection(debug=DEBUG)
        bucket = conn.get_bucket(self.bucket_name)
        prefix = '{year:4d}/{month:02d}/{day:02d}/{hour:02d}/audio_in-1-{year:4d}-{month:02d}-{day:02d}-{hour:02d}'.format(
                    year=self.year, month=self.month, day=self.day, hour=self.hour)
        bucket_list_result_set = bucket.list(prefix=prefix)
        print(bucket_list_result_set)
        the_iter = iter(bucket_list_result_set)
        for thing in the_iter:
            print(thing)
            # Find the minute we are looking for
            filename_details = thing.key[len(prefix)+1:]
            file_minute = int(filename_details[0:2])
            if (file_minute < minute):
                continue
            in_bytes = thing.get_contents_as_string(encoding=None)
            # Convert byte array to sample array
            if len(in_bytes) > 0:  # = self.samples_per_record:
                my_y = np.fromstring(in_bytes, np.float32)
                # Each record is chunk samples.
                # Convert back to an array of floats
                # Loop by step intervals, using a frame size of chunk samples
                for sample in range(0, int((len(my_y) - self.chunk)/self.step)):
                    my_y_subset = my_y[sample*self.step:sample*self.step+self.chunk-1:1]

                    # Send the samples out to anyone who is listening
                    self.output_queue.put_nowait(my_y_subset)
        self.output_queue.put_nowait(None)

if __name__ == '__main__':
    # execute only if run as a script
    # 'test_stream1446121778.355943'
    bucket = 'boyer-cs767-audio'
    output_queue = queue.Queue()
    player = ChunksFromS3(bucket_name=bucket, year=2015, month=11, day=5, hour=16, rate=96000, samples_per_record=96000/100, chunk=96000/40, step=96000/100, output_queue=output_queue)
    player.play_blob(19)
    player.play_blob(40)

    # output_queue should have samples
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=96000,
                    output=True)

    while True:
        data = output_queue.get(True)
        if data is not None:
            stream.write(data)
        else:
            break

    stream.stop_stream()
    stream.close()

    p.terminate()
