import time
import sys
import json
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

def main():
    face = Face()
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())
    memCache = MemoryContentCache(face)

    def onRegisterFailed(prefix):
        dump("Register failed for prefix", prefix.toUri())

    prefix = Name("/ndn/repo/case/test")

    dump("Register prefix", prefix.toUri())
    memCache.registerPrefix(prefix, onRegisterFailed, None, memCache.getStorePendingInterest())

    latestFrameNo = 0
    def generateFrame():
        data = Data(Name(prefix).append('s').append(Name.Component.fromSequenceNumber(latestFrameNo)))
        content = 'frame-data'
        data.setContent(content)
        metaInfo = MetaInfo()
        metaInfo.setFreshnessPeriod(30)
        data.setMetaInfo(metaInfo)
        keyChain.sign(data)
        dump("published frame", data.getName(), content)
        memCache.add(data)

    metaVersion = 0
    def updateMeta():
        data = Data(Name(prefix).append('_meta').append(Name.Component.fromVersion(metaVersion)))
        content = json.dumps({'timestamp':time.time(), 'stream':'s'})
        data.setContent(content)
        metaInfo = MetaInfo()
        metaInfo.setFreshnessPeriod(30)
        data.setMetaInfo(metaInfo)
        keyChain.sign(data)
        dump("update meta", data.getName(), content)
        memCache.add(data)

    def updateLatest(fNo):
        # data = Data(Name(prefix).append('_latest').append(Name.Component.fromVersion(metaVersion)))
        data = Data(Name(prefix).append('s').append('_latest').append(Name.Component.fromTimestamp(time.time()*1000)))
        content = Name(prefix).append('s').append(Name.Component.fromSequenceNumber(latestFrameNo)).toUri()
        data.setContent(content)
        metaInfo = MetaInfo()
        metaInfo.setFreshnessPeriod(10)
        data.setMetaInfo(metaInfo)
        keyChain.sign(data)
        dump("update _latest", data.getName(), content)
        memCache.add(data)

    metaUpdateInterval = 1
    frameGenerationInterval = 1/25
    latestUpdateInterval = 1/100
    timestampCheck = { 'meta':time.time(), 'frame_generate': time.time(), 'latest_ptr': time.time() }

    updateMeta()
    generateFrame()

    while True:
        now = time.time()

        if now - timestampCheck['meta'] >= metaUpdateInterval:
            timestampCheck['meta'] = now
            metaVersion += 1
            updateMeta()

        if now - timestampCheck['frame_generate'] >= frameGenerationInterval:
            timestampCheck['frame_generate'] = now
            latestFrameNo += 1
            generateFrame()

        if now - timestampCheck['latest_ptr'] >= latestUpdateInterval:
            timestampCheck['latest_ptr'] = now
            updateLatest(latestFrameNo)

        face.processEvents()
        time.sleep(0.001)

    face.shutdown()

main()