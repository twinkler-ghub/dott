# vim: set tabstop=4 expandtab :
###############################################################################
#   Copyright (c) 2019-2021 ams AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
###############################################################################

# Authors:
# - Thomas Winkler, ams AG, thomas.winkler@ams.com

import os
import struct


class BpSharedConf():
    # server-side port of TCP connection between MI and GDB process
    GDB_CMD_SERVER_PORT = 20080

class BpMsg():
    # header magic number
    MSG_HDR_MAGIC = b'\xd0\x11'

    # header length (2 bytes for magic, 1 byte for type and 2 bytes for payload length)
    MSG_HDR_LEN = 5

    # message types
    MSG_TYPE_HIT  = b'\x01'
    MSG_TYPE_FINISH_CONT = b'\x02'
    MSG_TYPE_EVAL = b'\x03'
    MSG_TYPE_EXEC = b'\x04'
    MSG_TYPE_EXCEPT = b'\x05'
    MSG_TYPE_RESP = b'\x06'

    def __init__(self, msg_type, payload=None):
        self._magic = BpMsg.MSG_HDR_MAGIC
        self._msg_type = msg_type
        self._payload = payload
        if payload is None:
            self._payload_len = 0
        else:
            self._payload_len = len(payload)

    def __str__(self):
        ret_val = os.linesep
        ret_val += 'magic: 0x%s, ' % self._magic.hex()
        ret_val += 'type:  0x%s, ' % self._msg_type.hex()
        ret_val += 'payload len: %d, ' % self._payload_len
        ret_val += 'payload: %s' % self._payload
        ret_val += os.linesep
        return ret_val

    def get_type(self):
        return self._msg_type

    def get_payload(self):
        return self._payload

    def get_payload_len(self):
        return self._payload

    @classmethod
    def read_from_socket(cls, sock, timeout=None):

        remaining = cls.MSG_HDR_LEN
        while remaining > 0:
            header = sock.recv(remaining)
            remaining -= len(header)

        magic = header[0:2]
        msg_type = header[2:3]
        payload_len = struct.unpack('H', header[3:5])[0]

        if magic != BpMsg.MSG_HDR_MAGIC:
            raise ValueError('Wrong header magic for breakpoint message.')

        payload = None
        if payload_len > 0:
            payload = b''
            remaining = payload_len
            while remaining > 0:
                payload += sock.recv(remaining)
                remaining = payload_len - len(payload)

        instance = cls(msg_type, payload)
        return instance

    def send_to_socket(self, sock):
        payload_len_bytes = struct.pack('H', self._payload_len)
        header = BpMsg.MSG_HDR_MAGIC + self._msg_type + payload_len_bytes
        sock.sendall(header)
        if self._payload_len > 0:
            sock.sendall(self._payload)


