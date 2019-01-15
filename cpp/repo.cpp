// g++ -o repo repo.cpp -std=c++11 -I../../ndnrtc-thirdparty/ndn-cpp/build/include -L../../ndnrtc-thirdparty/ndn-cpp/build/lib -lndn-cpp
#include <iostream>
#include <chrono>
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
  Name prefix("/ndn/repo/case/test");
  ptr_lib::shared_ptr<Data> savedMeta;

  face.registerPrefix(prefix,
    [&savedMeta](const ptr_lib::shared_ptr<const Name>& prefix,
       const ptr_lib::shared_ptr<const Interest>& interest, Face& face,
       uint64_t interestFilterId,
       const ptr_lib::shared_ptr<const InterestFilter>& filter)
      {
         if (interest->getName()[-1].toEscapedString() == "_meta")
         {
           cout << "NEEDED " << interest->getName() << endl;
           if (savedMeta)
           {
             cout << " > REPLY " << savedMeta->getName() << endl;
             face.putData(*savedMeta);
           }
           else
            cout << " > STORAGE EMPTY" << endl;
         }
       },
    [](const ptr_lib::shared_ptr<const Name>& prefix){
      cout << "register failed for prefix " << prefix << endl;
    });

    auto fetchMeta = [prefix, &savedMeta, &face](){
      Interest i(Name(prefix).append("_meta"));
      i.setMustBeFresh(true);
      i.setInterestLifetimeMilliseconds(3000);

      OnData onData = [&savedMeta](const ptr_lib::shared_ptr<const Interest>& interest,
        const ptr_lib::shared_ptr<Data>& data)
        {
          savedMeta = data;
          cout << " > SAVED " << data->getName() << " " << data->getContent().toRawStr() << endl;
        };

      cout << "REQUEST " << i.getName() << endl;
      face.expressInterest(i, onData);
    };

    int metaFetchInterval = 500;
    int64_t now = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
    int64_t timestampCheck = now;

    while (true) {
      now = duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
      if (now - timestampCheck >= metaFetchInterval)
      {
        timestampCheck = now;
        fetchMeta();
      }

      face.processEvents();
      usleep(10);
    }
}
