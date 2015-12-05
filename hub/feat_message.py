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
        for val in self.mfcc:
            self.buf += '{:f} '.format(val)
        return self.buf

    def decode(self, value):
        mfcc_strings = re.split(r'\s+', value.strip())
        self.mfcc = []
        for mfcc_string in mfcc_strings:
            self.mfcc.append(float(mfcc_string))
        return self.mfcc

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
    mfcc = numpy.arange(0, 5.55555555, 5.55555555/3, numpy.float32)
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

