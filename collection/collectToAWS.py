__author__ = 'jasonboyer'

import boto.kinesis
import pyaudio
import datetime

# From https://people.csail.mit.edu/hubert/pyaudio/docs/

"""PyAudio Example: Play a wave file (callback version)."""

import wave
import time
import sys
import base64


VERBOSE = False

if (VERBOSE) :
    import pprint
    pp = pprint.PrettyPrinter()

if len(sys.argv) < 2:
    print("Reads from the microphone, and writes to a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

# From https://gist.github.com/mabdrabo/8678538

FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
NUMRECORDS = int((RATE * RECORD_SECONDS) / CHUNK)


# instantiate PyAudio (1)
p = pyaudio.PyAudio()

waveFile = wave.open(sys.argv[1], 'wb')
waveFile.setnchannels(CHANNELS)
waveFile.setsampwidth(p.get_sample_size(FORMAT))
waveFile.setframerate(RATE)

# setup Amazon Kinesis upload
REGION = "us-east-1"
STREAMNAME = "audiomon"
if (VERBOSE):
    print("Kinesis regions: " + str(boto.kinesis.regions()))
kin = boto.kinesis.connect_to_region(REGION)
#kin = boto.kinesis.layer1.KinesisConnection(TargetPrefix="CS767/dcs")

if (VERBOSE):
    print("Available streams: " + str(kin.list_streams()))

# define callback (2)
numCallbacks = 0
#now = datetime.now()
seq = 0
startTime = 0
#    now.year()*1000000000000000 + \
#    now.month()*             100000000000 + \
#    now.day()*                 1000000000 + \
#    now.hour()*                  10000000 + \
#    now.minute()

if (VERBOSE):
    print("Starting sequence number: " + str(seq))

def callbackIn(in_data, frame_count, time_info, status):
    global numCallbacks
    global seq
    global startTime
    global kin

#    if (seq == 0) :
#        seq = time_info * 1000
#        startTime = time_info
#    else :
#        if (time_info > startTime) :
#            startTime = time_info
#            seq = startTime * 1000
#        else :
    seq = seq + 1

    if (VERBOSE) :
        print("frame_count: " + str(frame_count) + "time_info: " + str(time_info))

    if (VERBOSE) :
        pp.pprint(in_data)

    # for wav file. TODO: make wav/kinesis/other targets pluggable
    frames.append(in_data)

    b64In = base64.b64encode(in_data).decode('utf-8')

    if (VERBOSE) :
        pp.pprint(b64In)

    shardIdseq = kin.put_record(stream_name=STREAMNAME,
                                  data=b64In,
                                  #data=in_data,
                                  partition_key="1",
                                  sequence_number_for_ordering=str(seq),
                                  b64_encode=False
                                 )
    print("shardIdseq: " + str(shardIdseq))

    if  (seq > NUMRECORDS) :
        return None, pyaudio.paComplete
    else :
        return None, pyaudio.paContinue


# start Recording
streamIn = p.open(format=FORMAT, channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callbackIn)
print("recording...")
frames = []

# open stream using callback (3)
#streamOut = p.open(format=p.get_format_from_width(wf.getsampwidth()),
#                channels=wf.getnchannels(),
#                rate=wf.getframerate(),
#                output=True,
#                stream_callback=callbackOut)

# start the stream (4)
streamIn.start_stream()

# wait for stream to finish (5)
while streamIn.is_active():
    time.sleep(0.1)

# stop stream (6)
streamIn.stop_stream()
streamIn.close()
waveFile.writeframes(b''.join(frames))
waveFile.close()
# close PyAudio (7)
p.terminate()

