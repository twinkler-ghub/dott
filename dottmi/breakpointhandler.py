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

import queue
import threading
from typing import Dict

from dottmi.breakpoint import Breakpoint
from dottmi.gdb_mi import NotifySubscriber
from dottmi.utils import log


# -------------------------------------------------------------------------------------------------
class BreakpointHandler(NotifySubscriber, threading.Thread):
    def __init__(self) -> None:
        NotifySubscriber.__init__(self)
        threading.Thread.__init__(self, name='BreakpointHandler')
        self._breakpoints: Dict = {}
        self._running: bool = False

    def add_bp(self, bp: Breakpoint) -> None:
        self._breakpoints[bp.num] = bp

    def remove_bp(self, bp: Breakpoint) -> None:
        self._breakpoints.pop(bp.num)

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        while self._running:
            try:
                msg: Dict = self.wait_for_notification(True, timeout=0.1)
            except queue.Empty:
                continue

            if 'reason' in msg['payload']:
                payload = msg['payload']
                if payload['reason'] == 'breakpoint-hit':
                    bp_num = int(payload['bkptno'])
                    if bp_num in self._breakpoints:
                        self._breakpoints[bp_num].reached_internal(payload)
                    else:
                        log.warn(f'Breakpoint with number {bp_num} not found in list of known breakpoints.')
                else:
                    log.error(f'stop notification received with wrong reason: {payload["reason"]}')
