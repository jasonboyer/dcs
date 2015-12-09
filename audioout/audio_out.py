__author__ = 'jasonboyer'
""" Adapted from: https://people.csail.mit.edu/hubert/pyaudio/docs/
    PyAudio Example: Play a WAVE file."""

import pyaudio
import pydub
import wave
import sys

#CHUNK = 1024
CHUNK = 1

class AudioOut:
    def __init__(self, file, volume):
        filename, ext = file.split('.')
        self.file = filename + str(volume) + '.' + ext

    def play(self):
        wf = wave.open(self.file, 'rb')
        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        data = wf.readframes(CHUNK)

        while data != b'':
            stream.write(data)
            data = wf.readframes(CHUNK)

        stream.stop_stream()
        stream.close()

        p.terminate()

if __name__ == '__main__':
    file = 'thunder.wav'
    ao = AudioOut(file, 3)
    ao.play()