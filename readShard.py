__author__ = 'jasonboyer'

import boto.kinesis
import pyaudio

# From https://people.csail.mit.edu/hubert/pyaudio/#play-wave-callback-example
"""PyAudio Example: Play a wave file (callback version)."""

import wave
import time
import sys
import base64

VERBOSE = True

if VERBOSE:
    import pprint
    pp = pprint.PrettyPrinter()

# From https://gist.github.com/mabdrabo/8678538

FORMAT = pyaudio.paFloat32
CHANNELS = 2
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
NUMRECORDS = int((RATE * RECORD_SECONDS) / CHUNK)


# instantiate PyAudio (1)
p = pyaudio.PyAudio()

# setup Amazon Kinesis download
REGION = "us-east-1"
STREAMNAME = "audiomon"
if VERBOSE:
    print("Kinesis regions: " + str(boto.kinesis.regions()))
kin = boto.kinesis.connect_to_region(REGION)
shardit = kin.get_shard_iterator(stream_name=STREAMNAME,
                                 shard_id='shardId-000000000000',
                                 shard_iterator_type='AFTER_SEQUENCE_NUMBER',
                                 starting_sequence_number='49555268714976342660975793692755824344972400761954631682')


if VERBOSE:
    print("Available streams: " + str(kin.list_streams()))

# define callback (2)
numCallbacks = 0

wf = wave.open("foo.wav", "rb")


def callback_out(in_data, frame_count, time_info, status):
    global numCallbacks
    global seq
    global startTime
    global kin
    global shardit

    if VERBOSE:
        print("in_data: " + str(in_data) + "frame_count: " + str(frame_count) + "time_info: " + str(time_info) + "status: " + str(status))
        pp.pprint(in_data)

    records = kin.get_records(limit=int(frame_count/CHUNK), shard_iterator=shardit['ShardIterator'], b64_decode=False)

    if VERBOSE:
        print("getRecords returned records: " + str(records))

    shardit['ShardIterator'] = records['NextShardIterator']
    data = []

    for rec in records['Records']:
        pp.pprint(rec)
        data.append(base64.b64decode(rec['Data']))
#        data.append(rec['Data'])

    if data is None:
        return data, pyaudio.paComplete
    else:
        return b''.join(data), pyaudio.paContinue

stream = p.open(format=FORMAT,
                channels=2,
                rate=RATE,
                output=True,
                stream_callback=callback_out)

stream.start_stream()

while stream.is_active():
    time.sleep(0.1)

stream.stop_stream()
stream.close()

p.terminate()








