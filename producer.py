import time
from pyndn import Name
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain
from pyndn.meta_info import MetaInfo

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)

metaInfo = MetaInfo()
metaInfo.setFreshnessPeriod(30)

class Echo(object):
    def __init__(self, keyChain, certificateName):
        self._keyChain = keyChain
        self._certificateName = certificateName
        self._responseCount = 0

    def onInterest(self, prefix, interest, face, interestFilterId, filter):
        global metaInfo
        self._responseCount += 1

        dump("NEEDED ", interest.getName())

        if interest.getName()[-1].toEscapedString() == '_latest' :
            # Make and sign a Data packet.
            data = Data(interest.getName().append(Name.Component.fromTimestamp(time.time())))
            content = "latest pointer"

            data.setContent(content)
            data.setMetaInfo(metaInfo)
            self._keyChain.sign(data, self._certificateName)

            dump(" > REPLY", data.getName())
            face.putData(data)
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

    # Also use the default certificate name to sign data packets.
    echo = Echo(keyChain, keyChain.getDefaultCertificateName())
    prefix = Name("/ndn/repo/case")
    dump("Register prefix", prefix.toUri())
    face.registerPrefix(prefix, echo.onInterest, echo.onRegisterFailed)

    while True:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

main()