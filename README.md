## Run

On three machines connected to the same LAN segment:

1. Set up `PYTHONPATH`

```
export PYTHONPATH=`pwd`/thirdparty/PyNDN2/python:`pwd`/thirdparty/PyCNL/python:$PYTHONPATH
```

2. Start NFD

```
nfd-start &> /tmp/nfd.log
nfdc route add /ndn/repo/case <face-id>
```

* `face-id` -- ethernet face

3. Run scripts

* 1st machine:

```
python producer.py
```

* 2nd machine

```
python repo.py
```

* 3rd machine

```
python consumer.py
```
