import time, sys
from pyndn import Name, Face
from pyndn.util import Blob
from pyndn.util.common import Common
from pyndn.security import KeyChain, SafeBag
from pyndn.meta_info import MetaInfo
from pycnl import Namespace

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)

metaNumber = 1
def main():
    global metaNumber
    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    # Create an in-memory key chain with default keys.
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())

    publishIntervalMs = 30.0
    nmspc = Namespace("/ndn/repo/case/test", keyChain)

    dump("Register prefix", nmspc.name)
    # Set the face and register to receive Interests.
    nmspc.setFace(face,
      lambda prefixName: dump("Register failed for prefix", prefixName))

    metaInfo = MetaInfo()
    metaInfo.setFreshnessPeriod(30)

    def onObjectNeeded(namespace, neededNamespace, callbackID):
        global metaNumber
        dump("NEEDED", neededNamespace.name)
        timestamp = time.time()

        if neededNamespace.name[-1].toEscapedString() == '_meta':
            metaNamespace = neededNamespace[Name.Component.fromTimestamp(1547495389273.676)] 
            #metaNamespace = neededNamespace[Name.Component.fromTimestamp(time.time())] 
            #metaNamespace = neededNamespace[Name.Component.fromVersion(metaNumber)]
            metaNamespace.setNewDataMetaInfo(metaInfo)
            dump(" > REPLY META", metaNamespace.name)
            metaNamespace.serializeObject(Blob.fromRawStr("metadata"))
            metaNumber += 1
            return True

        # if neededNamespace.name[-1].toEscapedString() == '_latest':
        #     latestNamespace = neededNamespace[Name.Component.fromTimestamp(timestamp)]
        #     latestNamespace.setNewDataMetaInfo(metaInfo)
        #     dump(" > REPLY LATEST", latestNamespace.name)
        #     latestNamespace.serializeObject(Blob.fromRawStr("latest data pointer"))
        #     return True

        return False

    nmspc.addOnObjectNeeded(onObjectNeeded)

    # Loop, producing a new object every previousPublishMs milliseconds (and
    # also calling processEvents()).
    while True:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

main()
