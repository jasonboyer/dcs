__author__ = 'jasonboyer'
''' From https://github.com/jameslyons/python_speech_features example.py
'''
import sys
from features import mfcc
from features import logfbank
import scipy.io.wavfile as wav

if len(sys.argv) < 2:
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

(rate,sig) = wav.read(sys.argv[1])
mfcc_feat = mfcc(sig,rate)
fbank_feat = logfbank(sig,rate)

print(fbank_feat[1:3,:])
