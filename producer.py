import time
import sys
from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain
from pyndn.meta_info import MetaInfo
from pyndn.util import MemoryContentCache

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)

metaInfo = MetaInfo()
metaInfo.setFreshnessPeriod(30)

class Echo(object):
    def __init__(self, keyword, keyChain, certificateName, memCache):
        self._keyword = keyword
        self._keyChain = keyChain
        self._certificateName = certificateName
        self._responseCount = 0
        self._memCache = memCache

    def onDataNotFound(self, prefix, interest, face, interestFilterId, filter):
        global metaInfo
        self._responseCount += 1

        dump("NEEDED ", interest.getName())

        if interest.getName()[-1].toEscapedString() == self._keyword :

            if self._keyword == '_latest': 
                # add timestamp
                data = Data(interest.getName().append(Name.Component.fromTimestamp(time.time())))
            else:
                # fixed _meta
                data = Data(interest.getName().append(Name.Component.fromTimestamp(1547495389273.676)))
            content = "latest pointer"

            data.setContent(content)
            data.setMetaInfo(metaInfo)
            self._keyChain.sign(data, self._certificateName)

            dump(" > REPLY", data.getName())
            # face.putData(data)

            # SIMULATE: store pending interest
            self._memCache.storePendingInterest(interest, face)
            self._memCache.add(data)
        else:
            dump(" > IGNORE")

    def onRegisterFailed(self, prefix):
        self._responseCount += 1
        dump("Register failed for prefix", prefix.toUri())

def main():
    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    # Use the system default key chain and certificate name to sign commands.
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())
    memCache = MemoryContentCache(face)

    if sys.argv[1] == 'repo':
        echo = Echo('_meta', keyChain, keyChain.getDefaultCertificateName(), memCache)
    else:
        echo = Echo('_latest', keyChain, keyChain.getDefaultCertificateName(), memCache)

    prefix = Name("/ndn/repo/case/test")
    dump("Register prefix", prefix.toUri())
    memCache.registerPrefix(prefix, echo.onRegisterFailed, None, echo.onDataNotFound)

    while True:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

main()