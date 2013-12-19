# Realtime sound spectrograph built with Python, PyAudio, NumPy and OpenCV
# Cosmin Gorgovan <cosmin AT linux-geek.org>, Apr 16 2011
# Released into the public domain by the copyright holder

import pyaudio
import sys
import numpy as np
import cv2
import time
import math
# import pyo
import OSC

def averageList(lst):
    count = float(len(lst))
    s = 0.0
    for i in lst:
        s += i
    return s / count

client = OSC.OSCClient()
client.connect(('127.0.0.1', 1066))

CHUNK = 2048 # Samples
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100 # Samples per second

BPM = 100
BEATS = 4

LOWFREQ = 0
HIGHFREQ = 2000
FREQSTEP = float(RATE) / float(CHUNK) # inverse seconds (Hz)
LOWSAMPLE = int(math.floor(LOWFREQ/FREQSTEP))
HIGHSAMPLE = int(math.floor(HIGHFREQ/FREQSTEP))
SAMPLEDIFF = HIGHSAMPLE - LOWSAMPLE
BLOCKHEIGHT = 3
BLOCKWIDTH = 3
HEIGHT = SAMPLEDIFF*BLOCKHEIGHT

SAMPLECOUNT = ((60.0 / float(BPM)) * BEATS) * FREQSTEP # unitless (# of chunks)

# server = pyo.Server().boot()
# server.start()
# pitch = 440
# a = pyo.Sine(freq=pitch, mul=0.3).out()

# Spectrogram's width in pixels
NUMSAMPLES = 250
WINDOW_WIDTH = NUMSAMPLES * BLOCKWIDTH

AVERAGESAMPLES = 2

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

fftdata = np.zeros((SAMPLEDIFF, NUMSAMPLES), np.float)
avgdata = np.zeros((SAMPLEDIFF, NUMSAMPLES), np.float)
spectrogram = np.zeros((HEIGHT, WINDOW_WIDTH, 3), np.uint8)
maxlasttwenty = np.zeros(20, np.float)
cv2.namedWindow('image')
cv2.imshow('image', spectrogram)
highestV = 500000
accumulator = 0
frameswithdata = 0
avgfreqs = []
while(True):
    data = stream.read(CHUNK)
    data = np.fromstring(data, 'int16')
    ft = np.fft.rfft(data*np.hanning(len(data)))
    mgft = abs(np.real(ft))

    topwin1 = 0
    topwin1v = 0
    # topwin2 = 0
    # topwin2v = 0
    # topwin3 = 0
    # topwin3v = 0

    # DATA

    tmp = fftdata[0:SAMPLEDIFF, 1:NUMSAMPLES]
    fftdata[0:SAMPLEDIFF, 0:NUMSAMPLES-1] = tmp

    for i in range(LOWSAMPLE, HIGHSAMPLE):
        rvalue = mgft[i]
        fftdata[i - LOWSAMPLE, NUMSAMPLES-1] = rvalue
        # if rvalue > topwin1v:
            # topwin3 = topwin2
            # topwin3v = topwin2v
            # topwin2 = topwin1
            # topwin2v = topwin1v
            # topwin1 = i
            # topwin1v = rvalue
        # elif rvalue > topwin2v:
        #     topwin3 = topwin2
        #     topwin3v = topwin2v
        #     topwin2 = i
        #     topwin2v = rvalue
        # elif rvalue > topwin3v:
        #     topwin3 = i
        #     topwin3v = rvalue

    # DRAW

    tmp = avgdata[0:SAMPLEDIFF, 1:NUMSAMPLES]
    avgdata[0:SAMPLEDIFF, 0:NUMSAMPLES-1] = tmp

    tmp = spectrogram[0:HEIGHT, BLOCKWIDTH:WINDOW_WIDTH]
    spectrogram[0:HEIGHT, 0:WINDOW_WIDTH-BLOCKWIDTH] = tmp

    tmp = maxlasttwenty[1:20]
    maxlasttwenty[0:19] = tmp

    lastfew = fftdata[0:SAMPLEDIFF, NUMSAMPLES-AVERAGESAMPLES:NUMSAMPLES]
    avglastfew = lastfew.mean(1)

    maxlasttwenty[19] = np.nanmax(avglastfew) 
    ourV = max(np.nanmax(maxlasttwenty), highestV)

    framehasdata = 0
    frameavgfreq = 0.0
    frameavgfreqcount = 0.0
    for i in range(0, SAMPLEDIFF):
        # average = math.pow((avglastfew[i] / highestV), 0.5)
        average = math.pow((avglastfew[i] / ourV), 0.7)
        if average < 0.3:
            average = 0
        else:
            framehasdata = 1
            frameavgfreqcount += average
            frameavgfreq += i * FREQSTEP * average
            if average > topwin1v:
                topwin1v = average
                topwin1 = i
        avgdata[i, NUMSAMPLES-1] = average
        # average = math.pow(fftdata[i, NUMSAMPLES-1] / highestV, 0.5)
        # try:
        #     foo = int(average)
        # except:
        #     print(i)
        #     print(average)
        #     print(mgft[i + LOWSAMPLE])
        #     raise NameError("Boo!")

        # color = (int(SENSITIVITY*math.log10(rvalue+1)),0,int(255*(rvalue/highestV)))
        color = (0,0,int(255*average))
        for j in range(0,BLOCKHEIGHT):
            for k in range(0, BLOCKWIDTH):
                spectrogram[HEIGHT-1-i*BLOCKHEIGHT-j, WINDOW_WIDTH-1-k] = color
    frameswithdata += framehasdata
    if frameavgfreqcount != 0:
        avgfreqs.append(frameavgfreq/frameavgfreqcount)
    for j in range(0,BLOCKHEIGHT):
            for k in range(0, BLOCKWIDTH):
                spectrogram[HEIGHT-1-topwin1*BLOCKHEIGHT-j, WINDOW_WIDTH-1-k] = (0,255,topwin1v)
    # for j in range(0,BLOCKHEIGHT):
    #         for k in range(0, BLOCKWIDTH):
    #             spectrogram[HEIGHT-1-topwin2*BLOCKHEIGHT-j, WINDOW_WIDTH-1-k] = (int(SENSITIVITY*math.log10(topwin2v+1)),200,int(255*(topwin2v/highestV)))
    # for j in range(0,BLOCKHEIGHT):
    #         for k in range(0, BLOCKWIDTH):
    #             spectrogram[HEIGHT-1-topwin3*BLOCKHEIGHT-j, WINDOW_WIDTH-1-k] = (int(SENSITIVITY*math.log10(topwin3v+1)),150,int(255*(topwin3v/highestV)))
    cv2.imshow('image', spectrogram)
    k = cv2.waitKey(1)
    if k == 27:
        break
    elif k == 63232:
        pitch += 2
    elif k == 63233:
        pitch -= 2
        if pitch <= 100:
            pitch = 100

    accumulator += 1
    if accumulator >= SAMPLECOUNT:
        accumulator -= SAMPLECOUNT
        msg = OSC.OSCMessage()
        msg.setAddress("/pitch")
        print("------------")
        # a.setFreq(pitch)
        print(frameswithdata/SAMPLECOUNT)
        msg.append(frameswithdata/SAMPLECOUNT)
        frameswithdata = 0

        avgcount = len(avgfreqs)
        if avgcount < 4:
            print(0.0)
            msg.append(0.0)
        elif avgcount < 10:
            counts = int(avgcount / 2)
            startfreqs = avgfreqs[0:avgcount]
            startfreq = averageList(startfreqs)
            endfreqs = avgfreqs[-avgcount:]
            endfreq = averageList(endfreqs)
            print(endfreq - startfreq)
            msg.append(endfreq - startfreq)
        else:
            startfreqs = avgfreqs[0:5]
            startfreq = averageList(startfreqs)
            endfreqs = avgfreqs[-5:]
            endfreq = averageList(endfreqs)
            print(endfreq - startfreq)
            msg.append(endfreq - startfreq)
        avgfreqs = []

        for i in range(0,HEIGHT):
            col = spectrogram[i, WINDOW_WIDTH-1]
            spectrogram[i, WINDOW_WIDTH-1] = (255, col[0], col[1])

        client.send(msg)
      
client.close()
stream.stop_stream()
stream.close()
p.terminate()
