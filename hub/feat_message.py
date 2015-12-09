import boto.sqs.message
from hub import constants
import numpy
import re
import time


class FeatMessage(boto.sqs.message.Message):
    def __init__(self, body=None, queue=None):
        super()
        # body must be an array of floats
        self.mfcc = body
        self.buf = ''

    @property
    def message_attributes(self):
        return None

    def encode(self, value):
        self.buf = ''
        for val in value[0]:
            self.buf += '{:f} '.format(val)
        return self.buf

    def decode(self, value):
        mfcc_strings = re.split(r'\s+', value.strip())
        self.mfcc = [[]]
        for mfcc_string in mfcc_strings:
            self.mfcc[0].append(float(mfcc_string))
        return numpy.array(self.mfcc)

    def __len__(self):
        return len(self.buf)

    def get_body(self):
        return self.mfcc

    def set_body(self, body):
        self.mfcc = body


if __name__ == '__main__':
    # execute only if run as a script
    conn = boto.sqs.connect_to_region(constants.REGION)
    p = re.compile('\.')
    test_queue = conn.create_queue('test_queue'.join(p.split(str(time.time()))))
    test_queue.set_message_class(FeatMessage)
    mfcc = numpy.array([[ -7.32467121, -25.97041822, -50.75685508,  -1.40651625,
         -4.79041864,  57.36522094,  12.11778282, -48.33852065,
         45.76385218, -23.35362879, -15.63036292,  32.56883989,
         -8.71614269]])
    mess = FeatMessage(body=mfcc, queue=test_queue)
    test_queue.write(mess)
    done = False
    while done == False:
        rs = test_queue.get_messages()
        if (len(rs) == 0):
            time.sleep(1.0)
        else:
            break
    assert(len(rs) == 1)
    read_mess = rs[0]
    read_mfcc = read_mess.get_body()
    assert(numpy.allclose(mfcc, read_mfcc))
    conn.delete_queue(test_queue, force_deletion=True)

