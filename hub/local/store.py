from abc import ABCMeta, abstractmethod
import collection.collector

# Abstract interface to store a stream of audio data


class IStore(metaclass=ABCMeta):

    def __init__(self, audio_format, channels, rate, chunk, record_seconds):
        self.audio_format = audio_format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.record_seconds = record_seconds
        self.chunks_per_file = int(record_seconds * rate / chunk)
        self.collector = collection.collector.Collector(self.audio_format,
                                                        self.channels,
                                                        self.rate,
                                                        self.chunk,
                                                        self.record_seconds)

    @abstractmethod
    def store_data(self, indata):
        pass

    def start_storing(self):
        self.collector.start_collecting(self.store_data)

    def stop_storing(self):
        self.collector.stop_collecting()
