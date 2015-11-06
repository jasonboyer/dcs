__author__ = 'jasonboyer'
''' Adapted from http://www.mathworks.com/help/matlab/examples/fft-for-spectral-analysis.html
and http://practicalcryptography.com/miscellaneous/machine-learning/guide-mel-frequency-cepstral-coefficients-mfccs/
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
from matplotlib.backends.backend_pdf import PdfPages

pp = PdfPages('multipage.pdf')

if len(sys.argv) < 2:
    print("Imports a Matlab file.\n\nUsage: %s filename.mat" % sys.argv[0])
    sys.exit(-1)

file_name = sys.argv[1]



# mdict=matlabDict, appendmat=True,
matlabDict = scipy.io.loadmat(file_name, matlab_compatible=True)

#pp = pprint.PrettyPrinter()

#pp.pprint(matlabDict)

#RATE = 44100
#RATE = 48000
RATE = 96000
SAMPLE_SPACING = 1/RATE
CHUNK = int(RATE/40)  # 25 msec chunk
STEP = int(RATE/100)  # 10 msec step
FFTSIZE = 512
FFTKEEPSIZE = 257

myY = matlabDict['y']

for sample in range(0,int((myY.size - CHUNK)/STEP)):
    if sample > 210:
        time.sleep(1)
        plt.clf()
    myYSubset = myY[sample*STEP:sample*STEP+CHUNK-1:1]

    x = np.linspace(0.0, CHUNK * SAMPLE_SPACING, CHUNK)
    xf = np.linspace(0.0, 1/(2*SAMPLE_SPACING), CHUNK/2)
    xc = np.linspace(0.0, RATE/2, FFTKEEPSIZE)

    yf = fft(myYSubset, FFTSIZE)
    #yc = dct(myYSubset)
    ycc = np.multiply(np.abs(yf), np.abs(yf))
    ycc2 = np.divide(ycc, CHUNK)

    if sample > 209:
        #plt.plot(xf, 2.0/CHUNK * np.abs(yf[0:CHUNK/2]))
        plt.plot(xc[1:FFTKEEPSIZE], ycc2[1:FFTKEEPSIZE])
        #'Coordinates: {latitude}, {longitude}'.format(latitude='37.24N', longitude='-115.81W')
        title = '{file} time {time_start:.3f}-{time_end:.3f}'.format(
            file=file_name, time_start=STEP*sample/RATE, time_end=(STEP*sample+CHUNK)/RATE)
        plt.title(title)
        plt.xlabel("Hz")
        plt.grid()
        #pp.savefig()
        plt.show()




