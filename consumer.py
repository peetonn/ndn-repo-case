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

    name = Name("/ndn/repo/case")
    name.append(word)
    
    def request():
        dump("REQUEST", name.toUri())
        face.expressInterest(name, counter.onData, counter.onTimeout)
    request()
    nReceived = 0
    while True: #counter._callbackCount < 1:
        if nReceived < counter._callbackCount:
            nReceived = counter._callbackCount
            request()

        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

main()