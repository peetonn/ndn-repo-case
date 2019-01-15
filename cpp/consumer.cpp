//g++ -o consumer consumer.cpp -std=c++11 -I../../ndnrtc-thirdparty/ndn-cpp/build/include -L../../ndnrtc-thirdparty/ndn-cpp/build/lib -lndn-cpp
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

vector<string>& split(const string &s, char delim, vector<string> &elems) {
    stringstream ss(s);
    string item;
    while(getline(ss, item, delim))
        elems.push_back(item);
    return elems;
}

int main()
{
  Face face = Face();
  KeyChain keyChain = KeyChain();
  face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName());
  Name prefix("/ndn/repo/case/test");

  auto request = [&face](Name n, OnData onData, OnTimeout onTimeout){
    cout << "REQUEST " << n << endl;
    Interest i(n);
    i.setInterestLifetimeMilliseconds(3000);
    face.expressInterest(i, onData, onTimeout);
  };

  OnData onLatest;
  function<void(string, const ptr_lib::shared_ptr<const Interest>)>
    requestLatest = [prefix, request, &onLatest, &requestLatest](string stream, const ptr_lib::shared_ptr<const Interest> timeoutInterest){
      Name latestPrefix = Name(prefix).append(stream).append("_latest");
      request(latestPrefix, onLatest, ptr_lib::bind(requestLatest, stream, ptr_lib::placeholders::_1));
    };

  auto onMeta = [&requestLatest](const ptr_lib::shared_ptr<const Interest> interest, const ptr_lib::shared_ptr<Data> data){
    cout << " > RECEIVED _meta " << data->getName() << endl;
    vector<string> metaData;
    string stream = split(data->getContent().toRawStr(), ':', metaData)[0];
    requestLatest(stream, ptr_lib::shared_ptr<const Interest>());
  };

  function<void(const ptr_lib::shared_ptr<const Interest>)>
    requestMeta = [prefix, request, onMeta, &requestMeta](const ptr_lib::shared_ptr<const Interest> timeoutInterest){
      Name metaPrefix = Name(prefix).append("_meta");
      request(metaPrefix, onMeta, requestMeta);
    };

  Name framesPrefix;
  int latestFrame, ppSize = 3, pendingFrames = 0, nFetched;
  function<void()> fetchFrames;

  auto onNewFrame = [&pendingFrames, &nFetched, &fetchFrames](const ptr_lib::shared_ptr<const Interest> interest, const ptr_lib::shared_ptr<Data> data){
    pendingFrames--;
    nFetched++;
    fetchFrames();
    cout << " > RECEIVED frame " << data->getName() << endl;
  };

  function<void(const ptr_lib::shared_ptr<const Interest> i)>
  onFrameTimeout = [request, onNewFrame, &onFrameTimeout](const ptr_lib::shared_ptr<const Interest> i){
    cout << " > TIMEOUT frame " << i->getName() << endl;
    request(i->getName(), onNewFrame, onFrameTimeout);
  };

  fetchFrames = [ppSize, onNewFrame, onFrameTimeout, request, &pendingFrames, &latestFrame, &framesPrefix](){
    while (pendingFrames < ppSize) {
      if (framesPrefix.size() == 0)
        throw runtime_error("frames prefix is not set!");
      request(Name(framesPrefix).appendSequenceNumber(latestFrame), onNewFrame, onFrameTimeout);
      latestFrame++;
      pendingFrames++;
    }
  };

  onLatest = [fetchFrames, &latestFrame, &framesPrefix](const ptr_lib::shared_ptr<const Interest> interest, const ptr_lib::shared_ptr<Data> data){
    cout << " > RECEIVED _latest " << data->getContent().toRawStr() << endl;
    latestFrame = Name(data->getContent().toRawStr())[-1].toSequenceNumber();
    framesPrefix = Name(data->getContent().toRawStr()).getPrefix(-1);
    fetchFrames();
  };

  requestMeta(ptr_lib::shared_ptr<const Interest>());
  while (nFetched < 5) {
    face.processEvents();
    usleep(10);
  }

  face.shutdown();
}
