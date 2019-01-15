# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2018 Regents of the University of California.
# Author: Jeff Thompson <jefft0@remap.ucla.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU Lesser General Public License is in the file COPYING.

"""
This tests fetching a stream of generalized objects provided by
test_generalized_object_stream_producer (which must be running).
"""

import time, sys
from pyndn import Face
from pycnl import Namespace, NamespaceState
from pycnl.generalized_object import GeneralizedObjectStreamHandler

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)

run = True
requestLatest = False
def main():
    global requestLatest, run
    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    nmspc = Namespace("/ndn/repo/case/test")
    nmspc.setFace(face)

    def requestMeta():
        dump("REQUEST _meta")
        nmspc["_meta"].setMaxInterestLifetime(3000)
        nmspc["_meta"].objectNeeded(True)

    def namespaceStateChanged(namespace, changedNamespace, state, callbackId):
        global requestLatest, run
        dump("namespace state changed: ", namespace.name, changedNamespace.name, state)
        if state == NamespaceState.OBJECT_READY:
            if changedNamespace.name[-2].toEscapedString() == "_meta":
                requestMeta()
            dump(" > RECEIVED ", changedNamespace.name, changedNamespace.getObject().toRawStr())

        if state == NamespaceState.INTEREST_TIMEOUT:
            if changedNamespace.name[-1].toEscapedString() == "_meta":
                requestMeta()

    nmspc.addOnStateChanged(namespaceStateChanged)
    requestMeta()
    nmspc["_latest"].setMaxInterestLifetime(1000)

    while run:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

main()
