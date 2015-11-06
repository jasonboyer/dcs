__author__ = 'jasonboyer'
"""PyAudio Example: Play a WAVE file."""

import sys
import time
import numpy as np
from numpy import conj
import scipy.io
from scipy.fftpack import dct, idct
from scipy.fftpack import fft, ifft
import pyaudio
import pprint
import matplotlib.pyplot as plt

#CHUNK = 1024
CHUNK = 1

if len(sys.argv) < 2:
    print("Plays audio saved in a matlab file.\n\nUsage: %s filename.mat" % sys.argv[0])
    sys.exit(-1)

file_name = sys.argv[1]

matlabDict = scipy.io.loadmat(file_name, matlab_compatible=True)

pp = pprint.PrettyPrinter()

pp.pprint(matlabDict)

RATE = 44100
SAMPLE_SPACING = 1/RATE
CHUNK = int(RATE/4)  # 1/4 sec chunk

myY = matlabDict['y']

p = pyaudio.PyAudio()

stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=RATE,
                output=True)

for sample in range(0,int(myY.size/CHUNK)):
    data = myY[sample*CHUNK:(sample+1)*CHUNK-1:1]
    stream.write(data)

stream.stop_stream()
stream.close()

p.terminate()
