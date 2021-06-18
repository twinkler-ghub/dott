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

import logging
import os
import tempfile
from typing import List

import pylink
from pylink import JLink

from dottmi.dott import DottConf
from dottmi.dottexceptions import DottException


class _JlinkDott(JLink):

    def __init__(self, lib=None, log=None, detailed_log=None, error=None, warn=None, unsecure_hook=None):
        # decrease the log level for pylink to warning
        logging.getLogger("pylink").setLevel(logging.WARNING)

        if DottConf.get('jlink_path') is None:
            raise DottException('Live_access needs a local J-Link installation. JLink path is not set food DOTT config.')

        # Ensure that the same library (and hence the same JLinkDevices.xml) is used by pylink as by the GDB server.
        pylink.library.Library.find_library_windows = self._find_library
        pylink.library.Library.find_library_linux = self._find_library

        super().__init__(lib, log, detailed_log, error, warn, unsecure_hook)

        # create a reference to the folder which contains the JLinkDevices.xml (supporting relative flash loader paths)
        out_file_name = os.path.join(tempfile.gettempdir(), 'JLinkDevices.ref')
        with open(out_file_name, 'w') as out_file:
            out_file.write(os.path.dirname(self._library._path) + os.path.sep)

    def _find_library(self):
        """
        This function is used to override the corresponding function of pylink-square. The reason to do so
        is to ensure that pylink and gdb are using the same JLINK installation (and hence the same JLinkDevices.xml).
        """
        yield os.path.join(DottConf.get('jlink_path'), DottConf.get('jlink_lib_name'))


# -------------------------------------------------------------------------------------------------
class TargetDirect(object):
    def __init__(self, device_name: str):
        jlink_ip_addr = DottConf.get('jlink_server_addr')
        jlink_port = DottConf.get('jlink_server_port')
        jlink_serial = DottConf.get('jlink_serial')

        jlink_addr_port = f'{jlink_ip_addr}:{jlink_port}' if jlink_ip_addr is not None else None

        self._jlink = _JlinkDott()
        self._jlink.open(jlink_serial, jlink_addr_port)
        self._jlink.connect(device_name, verbose=False)

    def mem_read_32(self, addr: int, cnt: int = 1) -> int:
        """
        This function performs a 32bit memory read from target memory while the target is running.

        Args:
            addr: Target memory address to read from.
            cnt: Number of 32bit words to be read from the target.

        Returns: 32bit integer containing content read form target if cnt is 1, otherwise a list of 32bit integers
                 is returned.
        """
        self._jlink.halted()  # no-op required to ensure that pylink's state is in sync with the hardware
        ret = self._jlink.memory_read(addr, cnt, nbits=32)
        return ret[0] if len(ret) > 0 else ret

    def mem_write_32(self, addr: int, data: List) -> int:
        """
        This function performs a 32bit memory write to target memory while the target is running.
        Args:
            addr: Target memory address to write to.
            data: List of 32bit words to be written to the target starting at the provided address.

        Returns: The number of 32bit words written.

        """
        ret = self._jlink.memory_write(addr, data, nbits=32)
        return ret  # number of units written

    def disconnect(self) -> None:
        """
        This function closes te live access connection to the target.
        """
        self._jlink.close()

    @property
    def jlink_raw(self) -> JLink:
        """
        This property exposes the underlying PyLink instance. Use with care.
        """
        return self._jlink
