
import pyaudio
import wave
import time
import sys
import os
import collection.collector
from hub.local.store import IStore

# Store to disk in wav format


class StoreDisk(IStore):
    def __init__(self, audio_format, channels, rate, chunk, record_seconds, directory):
        super().__init__(audio_format, channels, rate, chunk, record_seconds)
        self.directory = directory
        self.chunks_per_file = int(record_seconds * rate / chunk)
        self.frames = []
        self.file_num = 1
        # TODO: catch exception
        # os.mkdir(directory)

    def store_data(self, indata):
        print('store_data(): len(frames): ' + str(len(self.frames)))
        self.frames.append(indata)
        if len(self.frames) >= self.chunks_per_file:
            # TODO: Move file I/O to an async thread
            wave_file = wave.open(self.directory +
                                  str(self.file_num),
                                  'wb')
            wave_file.setnchannels(self.channels)
            wave_file.setsampwidth(pyaudio.get_sample_size(self.audio_format))
            wave_file.setframerate(self.rate)
            wave_file.writeframes(b''.join(self.frames[:self.chunks_per_file]))
            wave_file.close()
            self.file_num += 1
            # move frame
            # TODO: Use a circular buffer or other appropriate data structure,
            # to avoid doing this move in the callback thread.
            temp_frame_buffer = self.frames[self.chunks_per_file:]
            self.frames = temp_frame_buffer

if __name__ == "__main__":
    # execute only if run as a script
    test_store = StoreDisk(pyaudio.paInt16, 1, 96000, 960, 5, 'Oct25')
    test_store.start_storing()
    time.sleep(30)
    test_store.stop_storing()
