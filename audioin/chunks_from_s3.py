''' Reconstructs sound samples from a Kinesis Firehose blob
'''

import time
import base64
import boto.s3
import boto.s3.connection
import audioin.chunks_from_bytes as cfb
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
        self.bytes_per_second = np.dtype(np.float32).itemsize * self.rate
        self.region = REGION
        if VERBOSE:
            print("Available S3 regions: ")
            print(boto.s3.regions())
        self.limit = 100

    def play_blob(self, start_minute=0, start_second=0,
                  requested_time=3600):
        converter = cfb.ChunksFromBytes(self.rate, self.chunk, self.step)
        conn = boto.s3.connection.S3Connection(debug=DEBUG)
        bucket = conn.get_bucket(self.bucket_name)
        prefix = '{year:4d}/{month:02d}/{day:02d}/{hour:02d}/audio_in-1-{year:4d}-{month:02d}-{day:02d}-{hour:02d}'.format(
                    year=self.year, month=self.month, day=self.day, hour=self.hour)
        bucket_list_result_set = bucket.list(prefix=prefix)
        print(bucket_list_result_set)
        total_time = 0
        total_bytes = 0
        remaining_bytes = requested_time * self.bytes_per_second
        # skip this many bytes before starting conversion
        start_offset = self.bytes_per_second * start_second
        the_iter = iter(bucket_list_result_set)
        for thing in the_iter:
            # Find the minute we are looking for
            # TODO: Should have a timestamp in the record for more accurate playback
            filename_details = thing.key[len(prefix)+1:]
            file_minute = int(filename_details[0:2])
            if file_minute < start_minute:
                continue
            print(thing)
            in_bytes = thing.get_contents_as_string(encoding=None)
            total_bytes += len(in_bytes)
            if total_bytes < start_offset:
                start_offset -= len(in_bytes)
                continue
            else:
                convert_bytes = in_bytes[start_offset:]
                start_offset = 0
            if remaining_bytes < len(convert_bytes):
                convert_bytes = convert_bytes[:remaining_bytes]
            remaining_bytes -= len(convert_bytes)
            # Convert byte array to sample array
            converter.process_bytes(convert_bytes, self.output_queue)
            # if len(convert_bytes) > 0:  # = self.samples_per_record:
            #    my_y = np.fromstring(in_bytes, np.float32)
            #    # Each record is chunk samples.
            #    # Convert back to an array of floats
            #    # Loop by step intervals, using a frame size of chunk samples
            #    for sample in range(0, int((len(my_y) - self.chunk)/self.step)):
            #        my_y_subset = my_y[sample*self.step:sample*self.step+self.chunk-1:1]

            #        total_time += self.step/self.rate
            #        if (total_time >= start_second):
            #            # Send the samples out to anyone who is listening
            #            self.output_queue.put_nowait(my_y_subset)
            #        if (total_time > requested_time):
            #            break
            if (remaining_bytes <= 0):
                break
        self.output_queue.put_nowait(None)

if __name__ == '__main__':
    # execute only if run as a script
    # 'test_stream1446121778.355943'
    bucket = 'boyer-cs767-audio'
    output_queue = queue.Queue()
    player = ChunksFromS3(bucket_name=bucket,
                          year=2015, month=11, day=10, hour=12,
                          rate=96000, samples_per_record=96000/100,
                          chunk=96000/40, step=96000/100,
                          output_queue=output_queue)
    player.play_blob(50, 53, 2)
#    player.play_blob(40)

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
