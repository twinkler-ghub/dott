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

import json

import gdb

from dottmi.gdb_shared import BpMsg, BpSharedConf

# global variable with all no-stop breakpoints
no_stop_bps = []


# ----------------------------------------------------------------------------------------------------------------------
class DottCmdInterceptPointCmds(gdb.Command):
    def __init__(self):
        super(DottCmdInterceptPointCmds, self).__init__("dott-bp-nostop-cmd", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        class InterceptPointCmds(gdb.Breakpoint):

            def __init__(self, func, commands):
                super(InterceptPointCmds, self).__init__(func)
                self._func = func
                self._commands = commands

            def get_func(self):
                return self._func

            def stop(self):
                try:
                    if self._commands is not None:
                        for cmd in self._commands:
                            gdb.execute(cmd)
                except Exception as e:
                    print("DOTT-CMD BP: gdb execute failed (%s)" % str(e))
                return False

            def close(self):
                # close method to expose same interface as normal NoStop breakpoint (as expected by delete command)
                pass

        try:
            # de-serialize breakpoint location and commands
            my_args = arg.replace('\\"', '"')
            my_args = json.loads(my_args)

            # create breakpoint and add it to the list
            bp = InterceptPointCmds(my_args[0], my_args[1:])
            global no_stop_bps
            no_stop_bps.append(bp)

        except Exception as ex:
            print(str(ex))


# ----------------------------------------------------------------------------------------------------------------------
class DottCmdInterceptPoint(gdb.Command):
    def __init__(self):
        super(DottCmdInterceptPoint, self).__init__("dott-bp-nostop-tcp", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):

        # No-Stop Breakpoint implementation executed in GDB context
        class InterceptPoint(gdb.Breakpoint):
            def __init__(self, func, sock):
                super(InterceptPoint, self).__init__(func)
                self._func = func
                self._sock = sock
                self._sock.setblocking(True)

            def get_func(self):
                return self._func

            def close(self):
                self._sock.close()
                self._sock = None

            def stop(self):
                stop_inferior = False

                if self._sock is None:
                    return stop_inferior

                try:
                    msg = BpMsg(BpMsg.MSG_TYPE_HIT) # bp hit message
                    msg.send_to_socket(self._sock)

                    while True:
                        # blocks until new message is available
                        msg = BpMsg.read_from_socket(self._sock)

                        # 'finish' message - resume target execution
                        if msg.get_type() == BpMsg.MSG_TYPE_FINISH_CONT:
                            stop_inferior = False
                            break

                        # 'execute' message
                        elif msg.get_type() == BpMsg.MSG_TYPE_EXEC:
                            try:
                                cmd = msg.get_payload().decode('ascii')
                                gdb.execute(cmd)
                                msg = BpMsg(BpMsg.MSG_TYPE_RESP)  # response message
                                msg.send_to_socket(self._sock)
                            except Exception as ex:
                                msg = BpMsg(BpMsg.MSG_TYPE_EXCEPT, str(ex))  # exception message
                                msg.send_to_socket(self._sock)

                        # 'eval' message
                        elif msg.get_type() == BpMsg.MSG_TYPE_EVAL:
                            try:
                                cmd = msg.get_payload().decode('ascii')
                                res = gdb.parse_and_eval(cmd)
                                pload = None
                                try:
                                    pload = str(int(res))
                                except:
                                    pload = str(res)
                                msg = BpMsg(BpMsg.MSG_TYPE_RESP, pload)  # response message
                                msg.send_to_socket(self._sock)
                            except Exception as ex:
                                msg = BpMsg(BpMsg.MSG_TYPE_EXCEPT, str(ex))  # exception message
                                msg.send_to_socket(self._sock)

                        else:
                            msg = BpMsg(BpMsg.MSG_TYPE_EXCEPT, 'Unknown breakpoint message type')
                            msg.send_to_socket(self._sock)

                except Exception as ex:
                    print('Execution of NoStopBreakpoint in GDB context failed.')
                    print(str(ex))

                # let target continue (stop_inferior = False) or halt the target
                return stop_inferior

        try:
            # connect to server socket (in MI process)
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', BpSharedConf.GDB_CMD_SERVER_PORT))

            # create breakpoint and add it to the list
            bp = InterceptPoint(arg, sock)
            global no_stop_bps
            no_stop_bps.append(bp)

        except Exception as ex:
            print(str(ex))


# ----------------------------------------------------------------------------------------------------------------------
class DottCmdInterceptPointDelete(gdb.Command):
    def __init__(self):
        super(DottCmdInterceptPointDelete, self).__init__("dott-bp-nostop-delete", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        global no_stop_bps

        if len(arg) == 0:
            # note: iterating over a copy of the list
            for bp in no_stop_bps[:]:
                bp.delete()  # delete function of gdb.Breakpoint
                bp.close()  # close down socket connection to MI process
                no_stop_bps.remove(bp)

        else:
            # note: iterating over a copy of the list
            for bp in no_stop_bps[:]:
                if arg.strip() == bp.get_func().strip():
                    bp.delete()  # delete function of gdb.Breakpoint
                    bp.close()  # close down socket connection to MI process
                    no_stop_bps.remove(bp)
                    break


# ----------------------------------------------------------------------------------------------------------------------
class DottCmdIsRunning(gdb.Command):
    def __init__(self):
        super(DottCmdIsRunning, self).__init__("dott-is-running", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        try:
            gdb.parse_and_eval('$pc')
            print('DOTT_RESP, %d, dott-is-running, NO, DOTT_RESP_END' % int(arg))
        except Exception as ex:
            print('DOTT_RESP, %d, dott-is-running, YES, %s, DOTT_RESP_END' % (int(arg), str(ex)))


# Initialize command(s)
DottCmdInterceptPointCmds()
DottCmdInterceptPoint()
DottCmdInterceptPointDelete()
DottCmdIsRunning()

