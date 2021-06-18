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
import sys
import socket
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../../../src/host')
# note: the dottmi imports have to be done after the sys path was adjusted (see line above)
from dottmi.fixtures import *  # note: it is important to fully import dottmi.fixtures
from dottmi.dott import DottConf

# set working directory to the folder which contains this conftest file
os.chdir(os.path.dirname(os.path.realpath(__file__)))


def set_config_options():
    # machine-specific settings (selected based on hostname)
    hostname = socket.gethostname()

    if hostname.lower() == 'd1380050c':
        # running on JENKINS slave
        DottConf.set('gdb_server_addr', '10.10.171.84')  # remote JLINK GDB Server (rpidott01)
        DottConf.set('jlink_server_addr', '10.10.171.84')  # remote JLINK connected to RaspberryPI (rpidott01)
        DottConf.set('pigpio_addr', '10.10.171.84')  # remote PiGPIO daemon on RaspberryPI (rpidott01)

    elif hostname.lower() == 'hbrd01':
        # running on Ubuntu Linux 20.04 Jenkins slave
        DottConf.set('jlink_serial', '000778832662')
        DottConf.set('pigpio_addr', '10.10.171.82')  # remote PiGPIO daemon on RaspberryPI (rpidott02)

    elif hostname.lower() == 'n1598046':
        # development machine
        pass

#    elif hostname == 'YOUR_HOST_NAME':
#        DottConf.set('gdb_server_addr', 'WWW.XXX.YYY.ZZZ')  # only needed for a remote JLINK connected to RaspberryPI
#        DottConf.set('pigpio_addr', 'AAA.BBB.CCC.DDD')  # remote PiGPIO daemon on RaspberryPI

# set host-specific parameters
set_config_options()

# re-target fixtures
target_reset = target_reset_flash
target_load = target_load_flash
