// g++ -o producer producer.cpp -std=c++11 -I../../ndnrtc-thirdparty/ndn-cpp/build/include -L../../ndnrtc-thirdparty/ndn-cpp/build/lib -lndn-cpp

#include <iostream>
#include <chrono>
#include <unistd.h>
#include <ndn-cpp/name.hpp>
#include <ndn-cpp/data.hpp>
#include <ndn-cpp/interest.hpp>
#include <ndn-cpp/security/key-chain.hpp>
#include <ndn-cpp/util/memory-content-cache.hpp>

using namespace std;
using namespace std::chrono;
using namespace ndn;

int main()
{
  Face face = Face();
  KeyChain keyChain = KeyChain();
  face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName());
  MemoryContentCache memCache = MemoryContentCache(&face);
  Name prefix("/ndn/repo/case/test");

  cout << "register prefix " << prefix << endl;
  memCache.registerPrefix(prefix,
    [](const ptr_lib::shared_ptr<const Name>& prefix){
      cout << "register failed" << endl;
    },
    memCache.getStorePendingInterest());

  int latestFrameNo = 0;
  function<void()> generateFrame = [prefix, &latestFrameNo, &keyChain, &memCache](){
    Data data(Name(prefix).append("s").appendSequenceNumber(latestFrameNo));
    data.setContent(Blob::fromRawStr("frame-data"));
    data.getMetaInfo().setFreshnessPeriod(30);
    keyChain.sign(data);

    cout << "published frame " << data.getName() << endl;
    memCache.add(data);
  };

  int metaVersion = 0;
  function<void()> updateMeta = [prefix, &metaVersion, &keyChain, &memCache](){
    int64_t now = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
    stringstream ss;
    ss << "s:" << now;

    Data data(Name(prefix).append("_meta").appendVersion(metaVersion));
    data.setContent(Blob::fromRawStr(ss.str()));
    data.getMetaInfo().setFreshnessPeriod(30);
    keyChain.sign(data);

    cout << "update _meta " << data.getName() << endl;
    memCache.add(data);
  };

  function<void()> updateLatest = [prefix, &latestFrameNo, &keyChain, &memCache](){
    int64_t now = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
    Data data(Name(prefix).append("s").append("_latest").appendTimestamp(now));
    data.setContent(Blob::fromRawStr(Name(prefix).append("s").appendSequenceNumber(latestFrameNo).toUri()));
    data.getMetaInfo().setFreshnessPeriod(10);
    keyChain.sign(data);

    cout << "update _latest " << data.getName() << endl;
    memCache.add(data);
  };

  double metaUpdateInterval = 1000;
  double frameGenerationInterval = 33;
  double latestUpdateInterval = 10;

  int64_t now = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
  map<string, int64_t> timestampCheck {{"meta", now},{"frame_generate", now}, {"latest_ptr", now}};

  updateMeta();
  generateFrame();

  while (true) {
    now = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();

    if (now - timestampCheck["meta"] >= metaUpdateInterval)
    {
      timestampCheck["meta"] = now;
      metaVersion += 1;
      updateMeta();
    }

    if (now - timestampCheck["frame_generate"] >= frameGenerationInterval)
    {
      timestampCheck["frame_generate"] = now;
      latestFrameNo += 1;
      generateFrame();
    }

    if (now - timestampCheck["latest_ptr"] >= latestUpdateInterval)
    {
      timestampCheck["latest_ptr"] = now;
      updateLatest();
    }

    face.processEvents();
    usleep(10);
  }
}
