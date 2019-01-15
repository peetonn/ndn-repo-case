import time
from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn import Interest
from pyndn.security import KeyChain
from pyndn.meta_info import MetaInfo

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)

metaInfo = MetaInfo()
metaInfo.setFreshnessPeriod(30)

savedMeta = None

class Echo(object):
    def __init__(self, keyChain, certificateName):
        self._keyChain = keyChain
        self._certificateName = certificateName
        self._responseCount = 0

    def onInterest(self, prefix, interest, face, interestFilterId, filter):
        global savedMeta
        self._responseCount += 1

        if interest.getName()[-1].toEscapedString() == '_meta' :
            dump("NEEDED ", interest.getName())
            if savedMeta:
                dump(" > REPLY ", savedMeta.getName())
                face.putData(savedMeta)
            else:
                dump(" > STORAGE EMPTY")
        elif interest.getName()[-1].toEscapedString() == '_latest' :
            dump("NEEDED ", interest.getName())
            dump(" > IGNORE")

    def onRegisterFailed(self, prefix):
        self._responseCount += 1
        dump("Register failed for prefix", prefix.toUri())

def main():
    face = Face()
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())

    echo = Echo(keyChain, keyChain.getDefaultCertificateName())
    prefix = Name("/ndn/repo/case/test")
    dump("Register prefix", prefix.toUri())
    face.registerPrefix(prefix, echo.onInterest, echo.onRegisterFailed)

    def fetchMeta():
        i = Interest(Name(prefix).append('_meta'))
        i.setMustBeFresh(True)
        i.setInterestLifetimeMilliseconds(3000)

        def onData(i, d):
            global savedMeta
            savedMeta = d 
            dump(' > SAVED', d.getName(), d.getContent().toRawStr())

        dump('REQUEST', i.getName())
        face.expressInterest(i, onData)

    metaFetchInterval = 1/2
    timestampCheck = { 'meta_fetch' : time.time() }

    while True:
        now = time.time()
        if now - timestampCheck['meta_fetch'] >= metaFetchInterval:
            timestampCheck['meta_fetch'] = now
            fetchMeta()

        face.processEvents()
        time.sleep(0.01)

    face.shutdown()

main()