import sys
import time
from pyndn import Name
from pyndn import Face

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

def main():
    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    counter = Counter()

    word = "_meta"

    nameMeta = Name("/ndn/repo/case/_meta")
    nameLatest = Name("/ndn/repo/case/_latest")
    
    def request(n):
        dump("REQUEST", n.toUri())
        face.expressInterest(n, counter.onData, counter.onTimeout)

    request(nameMeta)
    nReceived = 0

    currName = nameMeta
    while True: #counter._callbackCount < 1:
        if nReceived < counter._callbackCount:
            if nReceived == 0:
                currName = nameLatest
            nReceived = counter._callbackCount
            request(currName)

        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

main()