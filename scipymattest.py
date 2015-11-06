__author__ = 'jasonboyer'
''' Adapted from http://www.mathworks.com/help/matlab/examples/fft-for-spectral-analysis.html
'''

import sys
import time
import numpy as np
from numpy import conj
import scipy.io
from scipy.fftpack import dct, idct
from scipy.fftpack import fft, ifft
import pprint
import matplotlib.pyplot as plt

if len(sys.argv) < 2:
    print("Imports a Matlab file.\n\nUsage: %s filename.mat" % sys.argv[0])
    sys.exit(-1)

file_name = sys.argv[1]



# mdict=matlabDict, appendmat=True,
matlabDict = scipy.io.loadmat(file_name, matlab_compatible=True)

pp = pprint.PrettyPrinter()

pp.pprint(matlabDict)

RATE = 44100
SAMPLE_SPACING = 1/RATE
CHUNK = int(RATE/4)  # 1/4 sec chunk
FFTSIZE = 512
FFTKEEPSIZE = 257

myY = matlabDict['y']

for sample in range(0,int(myY.size/CHUNK)):
    if (sample > 1):
        time.sleep(1)
        plt.clf()
    myYSubset = myY[sample*CHUNK:(sample+1)*CHUNK-1:1]

    x = np.linspace(0.0, CHUNK * SAMPLE_SPACING, CHUNK)
    xf = np.linspace(0.0, 1/(2*SAMPLE_SPACING), CHUNK/2)
    xc = np.linspace(0.0, RATE/2, CHUNK/2)

    yf = fft(myYSubset)
    #yc = dct(myYSubset)
    #ycc = np.multiply(myYSubset, conj(myYSubset))
    ycc = np.multiply(yf, conj(yf))
    ycc2 = np.divide(ycc, CHUNK)

    if sample > 0:
        #plt.plot(xf, 2.0/CHUNK * np.abs(yf[0:CHUNK/2]))
        plt.plot(xc[1:int(CHUNK/2)], ycc2[1:int(CHUNK/2)])
        plt.grid()
        plt.show()




