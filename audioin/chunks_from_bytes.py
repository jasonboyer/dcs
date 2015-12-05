import numpy as np

class ChunksFromBytes:
    def __init__(self, rate, chunk, step):
        self.rate = rate
        self.chunk = chunk
        self.step = step

    def process_bytes(self, in_bytes, output_queue):
        # Convert byte array to sample array
        if len(in_bytes) > 0:  # = self.samples_per_record:
            my_y = np.fromstring(in_bytes, np.float32)
            # Each record is chunk samples.
            # Convert back to an array of floats
            # Loop by step intervals, using a frame size of chunk samples
            for sample in range(0, int((len(my_y) - self.chunk)/self.step)):
                my_y_subset = my_y[sample*self.step:sample*self.step+self.chunk-1:1]
                output_queue.put_nowait(my_y_subset)
