__author__ = 'jasonboyer'
''' Adapted from http://www.mathworks.com/help/matlab/examples/fft-for-spectral-analysis.html
and http://practicalcryptography.com/miscellaneous/machine-learning/guide-mel-frequency-cepstral-coefficients-mfccs/
'''

import sys
import time
import numpy as np
from numpy import conj
import scipy.io
from scipy.fftpack import fft, ifft
from scipy.io import wavfile as wf
import pprint
import matplotlib.pyplot as plt
import pyaudio
import wave

if len(sys.argv) < 2:
    print("Calculates MFCCs from a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

file_name = sys.argv[1]
infile = wf.read(file_name)
myY = np.array(infile[1], dtype=float)

p = pyaudio.PyAudio()

# TODO: how to get number of channels from wav file?
channels = 1

if channels > 1:
    print('Error: number of channels must be 1')
    exit()

RATE = infile[0]
SAMPLE_SPACING = 1/RATE
CHUNK = int(RATE/40)  # 25 msec chunk
STEP = int(RATE/100)  # 10 msec step
FFTSIZE = 512
FFTKEEPSIZE = 257


sample = 0

for sample in range(0,int(myY.size/CHUNK)):
    if sample > 84:
        time.sleep(1)
        plt.clf()

    myYSubset = myY[sample*CHUNK:(sample+1)*CHUNK-1:1]

    xc = np.linspace(0.0, RATE/2, FFTKEEPSIZE)

    yf = fft(myYSubset, FFTSIZE)
    ycc = np.multiply(np.abs(yf), np.abs(yf))
#    ycc = np.multiply(yf, conj(yf))
    ycc2 = np.divide(ycc, CHUNK)

    sample += 1

#    if sample > 83:
        #plt.plot(xf, 2.0/CHUNK * np.abs(yf[0:CHUNK/2]))
    plt.plot(xc[1:FFTKEEPSIZE], ycc2[1:FFTKEEPSIZE])
    title = '{file} time {time_start:.3f}-{time_end:.3f}'.format(
        file=file_name, time_start=STEP*sample/RATE, time_end=(STEP*sample+CHUNK)/RATE)
    plt.title(title)
    plt.xlabel("Hz")
    plt.grid()
    plt.show()




