import sys
import time
import json
from functools import partial
from pyndn import Name
from pyndn import Face
from pyndn import Interest

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)

class Counter(object):
    def __init__(self):
        self._callbackCount = 0

    def onData(self, interest, data):
        self._callbackCount += 1
        dump(" > RECEIVED", data.getName().toUri())
        # Use join to convert each byte to chr.
        dump(data.getContent().toRawStr())

    def onTimeout(self, interest):
        self._callbackCount += 1
        dump(" > TIMEOUT", interest.getName().toUri())

pendingFrames = 0
latestFrame = None
framesPrefix = None
def main():
    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    counter = Counter()

    prefix = Name("/ndn/repo/case/test")
    
    def request(n, onData, onTimeout):
        dump("REQUEST", n.toUri())
        interest = Interest(n)
        interest.setInterestLifetimeMilliseconds(3000)
        face.expressInterest(interest, onData, onTimeout)

    def onMeta(interest, data):
        dump(" > RECEIVED _meta", data.getName())
        stream = json.loads(data.getContent().toRawStr())['stream']
        requestLatest(stream)

    def requestMeta(arg = None):
        metaPrefix = Name(prefix).append('_meta')
        # STEP 2 - request _latest
        request(metaPrefix, onMeta, requestMeta)

    def onLatest(interest, data):
        global latestFrame, framesPrefix
        dump(" > RECEIVED _latest", data.getContent().toRawStr())
        latestFrame = Name(data.getContent().toRawStr())[-1].toSequenceNumber()
        framesPrefix = Name(data.getContent().toRawStr()).getPrefix(-1)
        fetchFrames()

    def requestLatest(stream, arg = None):
        latestPrefix = Name(prefix).append(stream).append('_latest')
        request(latestPrefix, onLatest, partial(requestLatest, stream))

    ppSize = 3
    def onNewFrame(interest, data):
        global pendingFrames
        pendingFrames -= 1
        fetchFrames()
        dump(" > RECEIVED frame", data.getName())

    def onFrameTimeout(interest):
        dump(" > TIMEOUT frame", interest.getName())
        request(interest.getName(), onNewFrame, onFrameTimeout)

    def fetchFrames():
        global pendingFrames, latestFrame, framesPrefix
        while pendingFrames < ppSize:
            if not framesPrefix:
                raise Exception('frame prefix is not set!')
            request(Name(framesPrefix).append(Name.Component.fromSequenceNumber(latestFrame)), onNewFrame, onFrameTimeout)
            latestFrame += 1
            pendingFrames += 1

    requestMeta()
    while True:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

main()