import sys
import time
import numpy as np
from scipy.fftpack import fft
from scipy.io import wavfile as wf
import pprint
import matplotlib.pyplot as plt

pp = pprint.PrettyPrinter()

#RATE = 44100
#RATE = 48000
RATE = 96000
SAMPLE_SPACING = 1/RATE
CHUNK = int(RATE / 40)  # 25 ms
INCREMENT = int(RATE / 10)  # 10 ms

if len(sys.argv) < 2:
    print("Imports a wav file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

file_name = sys.argv[1]

infile = wf.read(file_name)

myY = np.array(infile[1], dtype=float)

pp.pprint(myY)

pos = 0
while pos < myY.size and myY.size - pos > CHUNK:
    time.sleep(SAMPLE_SPACING * CHUNK)
    plt.clf()
    myYSubset = myY[pos:pos+CHUNK:1]

    x = np.linspace(0.0, CHUNK * SAMPLE_SPACING, CHUNK)
    xf = np.linspace(0.0, 1/(2*SAMPLE_SPACING), CHUNK/2)

    yf = fft(myYSubset)

    plt.plot(xf, 2.0/CHUNK * np.log(np.abs(yf[0:CHUNK/2])))
    plt.grid()
    if pos == 0:
        plt.show()
    pos += INCREMENT




