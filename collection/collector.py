__author__ = 'jasonboyer'
''' Collector class - reads audio data from default sound device
and forwards it to a storage facility
'''
import pyaudio
import time, datetime

VERBOSE = False
if VERBOSE:
    import pprint
    pp = pprint.PrettyPrinter()

class Collector:

    def __init__(self, audio_format, channels, rate, chunk, record_seconds):
        self.audio_format = audio_format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.record_seconds = record_seconds
        self.numCallbacks = 0
        self.seq = 0
        self.startTime = 0
        self.target = None
        self.stop_command_received = False
        self.p = pyaudio.PyAudio
        self.stream_in = None

    def start_collecting(self, target):
        # data is written to target in the callback
        self.target = target
        # instantiate PyAudio (1)
        self.p = pyaudio.PyAudio()
        # start Recording
        self.stream_in = self.p.open(format=self.audio_format,
                           channels=self.channels,
                           rate=self.rate,
                           input=True,
                           frames_per_buffer=self.chunk,
                           stream_callback=self.callback_in)
        if VERBOSE:
            print("recording...")

        # start the stream (4)
        self.stream_in.start_stream()

    def stop_collecting(self):
        self.stop_command_received = True
        # wait for stream to finish (5)
        while self.stream_in.is_active():
            time.sleep(0.1)

        # stop stream (6)
        self.stream_in.stop_stream()
        self.stream_in.close()

        # close PyAudio (7)
        self.p.terminate()

    def callback_in(self, in_data, frame_count, time_info, status):
        if self.stop_command_received:
            return None, pyaudio.paComplete
        if status == pyaudio.paInputUnderflow:
            print("INPUT UNDERFLOW: frame_count: " + str(frame_count) + "time_info: " + str(time_info))
        elif status == pyaudio.paInputOverflow:
            print("INPUT OVERFLOW: frame_count: " + str(frame_count) + "time_info: " + str(time_info))

        self.seq += 1
        if VERBOSE:
            print("frame_count: " + str(frame_count) + "time_info: " + str(time_info))
        # if VERBOSE:
            # pp.pprint(in_data)
        self.target(in_data)
        return None, pyaudio.paContinue


