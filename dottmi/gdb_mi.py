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
from pprint import pprint
from typing import Dict

from pygdbmi.gdbcontroller import GdbController

from dottmi.dottexceptions import DottException
from dottmi.utils import BlockingDict, log


# ----------------------------------------------------------------------------------------------------------------------
class GdbMi(object):
    def __init__(self, mi_controller: GdbController):
        self._mi_controller: GdbController = mi_controller

        # GDB machine interface context object used to track from what context GDB is currently accessed.
        self._mi_context: GdbMiContext = GdbMiContext()

        self._next_mi_token: int = 1000   # token used for MI communication
        self._next_cli_token: int = 8000  # id used for DOTT commands implemented in embedded python

        self._trace_commands: bool = False  # enable command tracing
        self._trace_total_walltime: float = 0.0

        # Dictionaries for different types of gdb responses.
        self._response_dicts: Dict[str, BlockingDict] = {'result': BlockingDict(),
                                                         'console': BlockingDict(),
                                                         'notify': BlockingDict()}

        # Create and start thread which handles the incoming response from GDB and puts
        # them into the correct response dictionary.
        self._response_handler = GdbMiResponseHandler(self._mi_controller, self._response_dicts)
        self._response_handler.start()

    ###############################################################################################
    # Properties
    @property
    def response_handler(self) -> 'GdbMiResponseHandler':
        """
        Returns the GDB MI response handler used by this object.

        Returns:
            GDB MI response handler object used by this object.
        """
        return self._response_handler

    @property
    def context(self) -> 'GdbMiContext':
        """
        Returns the GDB MI context used by this object.

        Returns:
            GDB MI context object used  by this object.
        """
        return self._mi_context

    ###############################################################################################
    # Helper functions to get the next CLI and MI tokens
    def _get_next_cli_token(self) -> int:
        ret = self._next_cli_token
        self._next_cli_token += 1
        return ret

    def _get_next_mi_token(self) -> int:
        ret = self._next_mi_token
        self._next_mi_token += 1
        return ret

    ###############################################################################################
    # Wrapper functions for GDB machine interface (mi)
    def _mi_wait_token_result(self, token: int, timeout: float = None) -> Dict:
        # the pop call is blocking; if timeout is not None a TimeoutError exception is raised
        msg = self._response_dicts['result'].pop(token, timeout)

        if (msg['message']) in ('done', 'running', 'stopped'):
            # Note: When operating GDB in async mode (as DOTT does it) 'running' and 'stopped' should be seen
            #       as equivalent ot 'done'. In fact, the notion of target state should only be based on notify
            #       messages (cp. https://sourceware.org/gdb/current/onlinedocs/gdb/GDB_002fMI-Result-Records.html#GDB_002fMI-Result-Records).
            return msg

        elif (msg['message']) == 'error':
            if 'stopped while in a function called from GDB' in msg['payload']['msg']:
                log.warn('Target execution was stopped by GDB. Likely reason: '
                         'A "HaltPoint" was hit while executing a target function using "eval". '
                         'Only use "InterceptPoint" breakpoints in this situation. '
                         '"HaltPoint" breakpoints shall only be used in "free running mode".')
            elif 'Unknown remote qXfer reply: OK' in msg['payload']['msg']:
                log.warn('Received message: %s' % msg['payload']['msg'])
            else:
                if 'Cannot execute this command while the target is running' in msg['payload']['msg']:
                    raise Exception('Target must be halted to execute the requested command!')
                else:
                    raise Exception("GDB Error: %s" % msg['payload']['msg'])

    def write_non_blocking(self, cmd: str) -> int:
        """
        Sends the provided command to GDB without blocking.
        Args:
            cmd: The command to be sent to GDB.

        Returns:
            The token which identifies the command sent to GDB. It is used to related GDB's response to the commands
            sent to it.
        """
        if self._mi_context.get_context() != GdbMiContext.NORMAL:
            if self._mi_context.get_context() == GdbMiContext.BP_INTERCEPT:
                # Provide a more specific error message when in InterceptPoint context.
                raise DottException('Cannot use normal DOTT commands to interact with the target while executing in '
                                    'InterceptPoint context. Instead, use eval/exec methods provided by the'
                                    'InterceptPoint implementation!')
            else:
                raise DottException('Cannot use normal DOTT commands to interact with the target while not executing '
                                    'NORMAL context!')

        token = self._get_next_mi_token()
        if self._trace_commands:
            log.debug(f'{token}         gdb write: {cmd}')
        try:
            self._mi_controller.write("%d%s" % (token, cmd), read_response=False)
        except IOError:
            log.warn('Got I/O error form gdb client! GDB session might have been closed prematurely due to previous '
                     'errors in this session. Check for any previous warning or error messages.')
        return token

    def write_blocking(self, cmd: str, timeout: float = None) -> Dict:
        """
        Sends the provided command to GDB and blocks until gdb returns with the result of the command.
        Args:
            cmd: The command to be sent to GDB.
            timeout: The amount of time to block at maximum while waiting for the response. If the timeout is reached,
            a TimeoutError exception is raised.

        Returns:
            The result of the command sent to GDB as a dictionary.
        """
        token = self.write_non_blocking(cmd)
        return self._mi_wait_token_result(token, timeout)

    def shutdown(self) -> None:
        """
        Stops the gdb response handler.
        """
        self._response_handler.stop()


# ----------------------------------------------------------------------------------------------------------------------
class GdbMiContext(object):
    """
    This class is used to represent the context of a host to gdb connection. It is used internally by DOTT.
    """
    NORMAL = 0x01
    BP_INTERCEPT = 0x02

    def __init__(self):
        self._context_lock: threading.Lock = threading.Lock()
        self._context: int = GdbMiContext.NORMAL
        self._context_holder = None

    def acquire_context(self, context_holder, context: int) -> None:
        with self._context_lock:
            if self._context != GdbMiContext.NORMAL:
                raise DottException('Unable to switch context while not in normal context.'
                                    'Current context holder has to release first.')
            else:
                self._context = context
                self._context_holder = context_holder

    def release_context(self, context_holder):
        with self._context_lock:
            if context_holder != self._context_holder:
                raise DottException('Context can only be released from the the same '
                                    'entity that did the previous context setting.')
            else:
                self._context = GdbMiContext.NORMAL
                self._context_holder = None

    def get_context(self) -> int:
        with self._context_lock:
            return self._context


# ----------------------------------------------------------------------------------------------------------------------
class GdbMiResponseHandler(threading.Thread):
    def __init__(self, mi_controller: GdbController, dicts: Dict) -> None:
        super().__init__(name='GdbResponseHandler')
        self._mi_controller = mi_controller
        self._response_dicts = dicts
        self._running = False
        self._notify_subscribers = {}

    def notify_subscribe(self, subscriber, notify_msg: str, notify_reason: str = None) -> None:
        if (notify_msg, notify_reason) not in self._notify_subscribers:
            self._notify_subscribers[(notify_msg, notify_reason)] = []
        self._notify_subscribers[(notify_msg, notify_reason)].append(subscriber)

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True

        while self._running:
            try:
                messages = self._mi_controller.get_gdb_response(timeout_sec=0.005, raise_error_on_timeout=False)

                for msg in messages:
                    msg_type = str(msg['type']).lower()
                    # log.debug('[MSG] %s' % msg)

                    if msg_type == 'result':
                        msg_token = -1
                        if 'token' in msg:
                            msg_token = msg['token']
                            # log.debug('[MSG] %s' % msg)
                        else:
                            log.warn('result w/o token: ')
                            pprint(msg)
                        self._response_dicts['result'].put(msg_token, msg)

                    elif msg_type == 'console':
                        if 'payload' in msg:
                            payload = msg['payload']
                            if 'DOTT_RESP' in payload:
                                resp_id = (int(payload.split(',')[1]))
                                self._response_dicts['console'].put(resp_id, msg)
                        else:
                            self._response_dicts['console'].put(0, msg)
                        # log.debug('[CON] %s' % bytes(msg['payload'], 'ascii').decode('unicode_escape').rstrip())

                    elif msg_type == 'output':
                        pass
                        # log.debug('[OUT] %s' % bytes(msg['payload'], 'ascii').decode('unicode_escape').rstrip())

                    elif msg_type == 'target':
                        pass
                        # log.debug("[TARGET] %s", msg['payload'])

                    elif msg_type == 'notify':
                        notify_msg = msg['message']  # e.g., 'stopped', 'running', ...
                        # log.info("[NOTIFY] %s", msg)

                        notify_reason = None
                        if 'reason' in msg['payload']:
                            notify_reason = msg['payload']['reason']

                        already_notified = []
                        if (notify_msg, notify_reason) in self._notify_subscribers:
                            for subscriber in self._notify_subscribers[(notify_msg, notify_reason)]:
                                subscriber.notify(msg)
                                already_notified.append(subscriber)
                        if (notify_msg, None) in self._notify_subscribers:
                            for subscriber in self._notify_subscribers[(notify_msg, None)]:
                                if subscriber not in already_notified:
                                    subscriber.notify(msg)

                        # if there are no subscribers for this notification it is stored in a dict for later analysis
                        if len(already_notified) == 0:
                            self._response_dicts['notify'].put((notify_msg, notify_reason), msg)

                    elif msg_type == 'log':
                        pass
                        # log.debug("[LOG] %s", msg['payload'])

                    else:
                        log.warn(f'Unknown message type: {msg_type}')
                        log.warn(f'Full message: {msg}')

            except IOError as ex:
                log.exception(ex)
                raise ex

            except Exception as ex:
                log.exception(ex)
                raise ex


# ----------------------------------------------------------------------------------------------------------------------
class NotifySubscriber(object):
    def __init__(self):
        self._notifications: queue.Queue = queue.Queue()

    def notify(self, msg: Dict) -> None:
        self._notifications.put(msg)
        # Note: Callback handlers are executed in own thread to ensure that main gdbmi thread is not blocked. This is
        # important as callback handlers can issue their own GDB requests which might lead to deadlocks if callback
        # handlers are called in gdbmi context.
        threading.Thread(target=self._notify_callback).start()

    def _notify_callback(self):
        pass

    def wait_for_notification(self, block: bool = True, timeout: float = None) -> Dict:
        """
        Args:
            block: True to block while waiting for notification, False otherwise.
            timeout: If blocking, specify the timeout when the function returns without having received and event.

        Returns: Dict which was received.
        """
        return self._notifications.get(block, timeout)
