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

from abc import ABC

from dottmi.dottexceptions import DottException
from dottmi.pylinkdott import JlinkDott


class TargetAdapterBase(ABC):
    pass


class TargetAdapterPylink(TargetAdapterBase):
    def __init__(self, jlink_srv_addr: str, jlink_srv_port: int, jlink_serial: int, device_name: str):
        self._jlink_srv_addr: str = jlink_srv_addr
        self._jlink_srv_port: int = jlink_srv_port
        self._jlink_serial: int = jlink_serial
        self._device_name: str = device_name

        jlink_addr_port = f'{self._jlink_srv_addr}:{self._jlink_srv_port}' if self._jlink_srv_addr is not None else None
        self._jlink = JlinkDott()
        self._jlink.open(jlink_serial, jlink_addr_port)
        self._jlink.connect(device_name, verbose=True)

    def mem_read(self, src_addr: int, num_bytes: int) -> bytes:
        self._jlink.halted()  # no-op required to ensure that pylink's state is in sync with the hardware
        ret = self._jlink.memory_read(src_addr, num_bytes)
        return bytes(ret)

    def mem_write(self, dst_addr: int, data: bytes) -> None:
        ret = self._jlink.memory_write(dst_addr, list(data))
        self._jlink.jtag_flush()
        if ret != len(data):
            raise DottException('Memory write to target unsuccessful!')
