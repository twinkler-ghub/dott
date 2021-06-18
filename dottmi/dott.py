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

import configparser
import glob
import os
import os.path
import platform
import socket
import subprocess
import sys
import types
from ctypes import CDLL
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import List, Tuple

from dottmi.dottexceptions import DottException
from dottmi.target_mem import TargetMemModel
from dottmi.utils import log, log_setup, singleton


class DottHooks(object):
    _pre_connect_hook: types.FunctionType = None

    @classmethod
    def set_pre_connect_hook(cls, pre_connect_hook: types.FunctionType) -> None:
        cls._pre_connect_hook = pre_connect_hook

    @classmethod
    def exec_pre_connect_hook(cls) -> None:
        if cls._pre_connect_hook is not None:
            cls._pre_connect_hook()

# ----------------------------------------------------------------------------------------------------------------------
@singleton
class Dott(object):

    def __init__(self) -> None:
        self._default_target = None
        self._all_targets: List = []

        # initialize logging subsystem
        log_setup()

        # read and pre-process configuration file
        DottConf.parse_config()

        # the port number used by the internal auto port discovery; discovery starts at config's gdb server port
        self._next_gdb_srv_port: int = int(DottConf.conf['gdb_server_port'])

        # Hook called before the first debugger connection is made
        DottHooks.exec_pre_connect_hook()

        self._default_target = self.create_target(DottConf.conf['device_name'], DottConf.conf['jlink_serial'])

    def _get_next_srv_port(self, srv_addr: str) -> int:
        """
        Find the next triplet of free ("bind-able") TCP ports on the given server IP address.
        Ports are automatically advanced unit a free port triplet is found.

        Args:
            srv_addr: IP address of the server.
        Returns:
            Returns the first port number of the discovered, free port triplet.
        """
        port = self._next_gdb_srv_port
        sequentially_free_ports = 0
        start_port = 0

        while True:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind((srv_addr, port))
                sequentially_free_ports += 1
                if sequentially_free_ports == 1:
                    start_port = port
            except socket.error:
                # log.debug(f'Can not bind port {port} as it is already in use.')
                sequentially_free_ports = 0
            finally:
                s.close()

            if sequentially_free_ports > 2:
                # JLINK GDB server needs 3 free ports in a row
                break

            port += 1
            if port >= 65535:
                raise DottException(f'Unable do find three (consecutive) free ports for IP {srv_addr}!')

        self._next_gdb_srv_port = start_port + sequentially_free_ports
        if self._next_gdb_srv_port > 65500:
            self._next_gdb_srv_port = int(DottConf.conf['gdb_server_port'])
        return start_port

    def create_gdb_server(self, dev_name: str, jlink_serial: str = None, srv_addr: str = None, srv_port: int = -1) -> 'GdbServer':
        """
        Factory method to create a new GDB server instance. The following parameters are defined via DottConfig:
        gdb_server_binary, jlink_interface, device_endianess, jlink_speed, and jlink_server_addr.

        Args:
            dev_name: Device name as in JLinkDevices.xml
            jlink_serial: JLINK serial number.
            srv_addr: Server address.
            launch: Whether or not to launch the GDB server process.
        Returns:
            The created GdbServer instance.
        """
        from dottmi.gdb import GdbServerJLink

        if srv_port == -1:
            srv_port = int(DottConf.conf['gdb_server_port'])

        if srv_addr is None:
            srv_addr = DottConf.conf['gdb_server_addr']

        if srv_addr is None:
            # if gdb server is launched by DOTT, we determine the port ourselves
            srv_port = self._get_next_srv_port('127.0.0.1')

        gdb_server = GdbServerJLink(DottConf.conf['gdb_server_binary'],
                                    srv_addr,
                                    srv_port,
                                    dev_name,
                                    DottConf.conf['jlink_interface'],
                                    DottConf.conf['device_endianess'],
                                    DottConf.conf['jlink_speed'],
                                    jlink_serial,
                                    DottConf.conf['jlink_server_addr'])

        return gdb_server

    def create_target(self, dev_name: str, jlink_serial: str = None) -> 'Target':
        from dottmi import target
        from dottmi.gdb import GdbClient

        srv_addr = DottConf.conf['gdb_server_addr']

        try:
            gdb_server = self.create_gdb_server(dev_name, jlink_serial, srv_addr=srv_addr)

            # start GDB Client
            gdb_client = GdbClient(DottConf.conf['gdb_client_binary'])
            gdb_client.connect()

            # create target instance and set GDB server address
            target = target.Target(gdb_server, gdb_client)

        except TimeoutError:
            target = None

        # add target to list of created targets to enable proper cleanup on shutdown
        if target:
            self._all_targets.append(target)
        return target

    @property
    def target(self):
        return self._default_target

    @target.setter
    def target(self, target: object):
        raise ValueError('Target can not be set directly.')

    def shutdown(self) -> None:
        for t in self._all_targets:
            t.disconnect()
        self._all_targets = []


# ----------------------------------------------------------------------------------------------------------------------
# For backwards compatibility reasons the Dott() singleton can also be accessed via the all lowercase dott function.
def dott() -> Dott:
    return Dott()


# ----------------------------------------------------------------------------------------------------------------------
# Central Dott configuration registry. Data is read in from dott ini file. Additional settings can be made via
# project specific conftest files.
class DottConf:
    conf = {}
    dott_runtime = None

    @staticmethod
    def set(key: str, val: str) -> None:
        DottConf.conf[key] = val

    @staticmethod
    def set_runtime_if_unset(dott_runtime_path: str) -> None:
        if not os.path.exists(dott_runtime_path):
            raise ValueError(f'Provided DOTT runtime path ({dott_runtime_path}) does not exist.')
        if os.environ.get('DOTTRUNTIME') is None:
            os.environ['DOTTRUNTIME'] = dott_runtime_path

    @staticmethod
    def get(key: str):
        return DottConf.conf[key]

    @staticmethod
    def _setup_runtime():
        DottConf.set('DOTTRUNTIME', None)

        dott_runtime_path = sys.prefix + os.sep + 'dott_data'
        if os.path.exists(dott_runtime_path):
            runtime_version: str = 'unknown'
            with Path(dott_runtime_path + '/apps/version.txt').open() as f:
                line = f.readline()
                while line:
                    if 'version:' in line:
                        runtime_version = line.lstrip('version:').strip()
                        break
                    line = f.readline()
            os.environ['DOTTGDBPATH'] = str(Path(f'{dott_runtime_path}/apps/gdb/bin'))
            os.environ['PYTHONPATH27'] = str(Path(f'{dott_runtime_path}/apps/python27/python-2.7.13'))
            DottConf.set('DOTTRUNTIME', f'{dott_runtime_path} (dott-runtime package)')
            DottConf.set('DOTT_RUNTIME_VER', runtime_version)
            DottConf.set('DOTTGDBPATH', str(Path(f'{dott_runtime_path}/apps/gdb/bin')))
            DottConf.set('PYTHONPATH27', str(Path(f'{dott_runtime_path}/apps/python27/python-2.7.13')))

            # Linux: check if libpython2.7 and libnurses5 are installed. Windows: They are included in the DOTT runtime.
            if platform.system() == 'Linux':
                res = os.system(str(Path(f'{dott_runtime_path}/apps/gdb/bin/arm-none-eabi-gdb-py')))
                if res != 0:
                    raise DottException('Unable to start gdb client. This might be caused by missing dependencies.\n'
                                        'Make sure that libpython2.7 and libncurses5 are installed.')

        # If DOTTRUNTIME is set in the environment it overrides the integrated runtime in dott_data
        if os.environ.get('DOTTRUNTIME') is not None and os.environ.get('DOTTRUNTIME').strip() != '':
            dott_runtime_path = os.environ.get('DOTTRUNTIME')
            dott_runtime_path = dott_runtime_path.strip()
            DottConf.set('DOTTRUNTIME', dott_runtime_path)

            if not os.path.exists(dott_runtime_path):
                raise ValueError(f'Provided DOTT runtime path ({dott_runtime_path}) does not exist.')
            try:
                DottConf.dott_runtime = SourceFileLoader('dottruntime', dott_runtime_path + os.sep + 'dottruntime.py').load_module()
                DottConf.dott_runtime.setup()
                DottConf.set('DOTT_RUNTIME_VER', DottConf.dott_runtime.DOTT_RUNTIME_VER)
            except Exception as ex:
                raise Exception('Error setting up DOTT runtime.')

        if DottConf.get('DOTTRUNTIME') is None:
            raise Exception('Runtime components neither found in DOTT data path nor in DOTTRUNTIME folder.')

    @staticmethod
    def _get_jlink_path(segger_path: str, segger_lib_name: str) -> Tuple[str, str, int]:
        all_libs = {}
        libs = glob.glob(os.path.join(segger_path, '**', segger_lib_name), recursive=True)

        for lib in libs:
            try:
                clib = CDLL(lib)
            except OSError:
                # Note: On Linux, Segger provides symlinks in the x86 folder to the 32bit version of the the 
                # JLink library using the 64bit library name. Attempting to load this library on a 64bit system
                # results in an exception.
                continue
            ver = clib.JLINKARM_GetDLLVersion()
            all_libs[ver] = lib

        jlink_path: str = ''
        jlink_version: str = '0'
        if len(all_libs) > 0:
            jlink_version = (sorted(all_libs.keys())[-1:])[0]
            jlink_path = all_libs.get(jlink_version)
            jlink_path = os.path.dirname(jlink_path)

            #                       6.50   6.50b  6.52   6.52a  6.52b  6.52c
            known_issue_versions = (65000, 65020, 65200, 65210, 65220, 65230)
            if jlink_version in known_issue_versions:
                log.warn(f'The J-Link software with the highest version (in {jlink_path}) has known '
                         f'issues related to SRAM download and STM32 MCUs. Please upgrade to at least v6.52d')
        else:
            raise DottException(f'JLink software (esp. {segger_lib_name}) not found in path {segger_path}.')
        jlink_version = f'{str(jlink_version)[:1]}.{str(jlink_version)[1:3]}{chr(int(str(jlink_version)[-2:]) + 0x60)}'

        return jlink_path, segger_lib_name, jlink_version

    @staticmethod
    def parse_config():
        # setup runtime environment
        DottConf._setup_runtime()
        log.info(f'DOTT runtime:          {DottConf.get("DOTTRUNTIME")}')
        log.info(f'DOTT runtime version:  {DottConf.get("DOTT_RUNTIME_VER")}')

        # print working directory
        log.info(f'work directory:        {os.getcwd()}')

        # default ini file
        dott_section = 'DOTT'
        dott_ini = 'dott.ini'

        # JLINK gdb server
        if platform.system() == 'Linux':
            jlink_default_path = str(Path('/opt/SEGGER'))
            jlink_gdb_server_binary = 'JLinkGDBServerCLExe'
            jlink_lib_name = 'libjlinkarm.so'
        else:
            jlink_default_path = str(Path('C:/Program Files (x86)/SEGGER'))
            jlink_gdb_server_binary = 'JLinkGDBServerCL.exe'
            jlink_lib_name = 'JLink_x64.dll'

        # the DOTTJLINKPATH environment variable overrides the default location of the Segger JLink package
        if 'DOTTJLINKPATH' in os.environ.keys():
            log.info(f'Overriding default JLink path ({jlink_default_path}) with DOTTJLINKPATH ({os.environ["DOTTJLINKPATH"]})')
            jlink_default_path = os.environ['DOTTJLINKPATH']

        # if a dott.ini is found in the working directory then parse it
        if os.path.exists(os.getcwd() + os.sep + dott_ini):
            # read ini file
            ini = configparser.ConfigParser()
            ini.read(os.getcwd() + os.sep + dott_ini)

            if not ini.has_section(dott_section):
                raise Exception(f'Unable to find section DOTT in {dott_ini}')

            # create an in-memory copy of the DOTT section of the init file
            conf_tmp = dict(ini[dott_section].items())

        else:
            log.info(f'No dott.ini found in working directory.')
            conf_tmp = {}

        # only copy items from ini to in-memory config which are not already present (i.e., set programmatically)
        for k, v in conf_tmp.items():
            if k not in DottConf.conf.keys():
                DottConf.conf[k] = v

        # Go through the individual config options and set reasonable defaults
        # where they are missing (or return an error)

        if 'bl_load_elf' not in DottConf.conf:
            DottConf.conf['bl_load_elf'] = None
        if DottConf.conf['bl_load_elf'] is not None:
            if not os.path.exists(DottConf.conf['bl_load_elf']):
                raise ValueError(f'{DottConf.conf["bl_load_elf"]} does not exist.')
        log.info(f'BL ELF (load):         {DottConf.conf["bl_load_elf"]}')

        if 'bl_symbol_elf' not in DottConf.conf:
            # if no symbol file is specified assume that symbols are contained in the load file
            DottConf.conf['bl_symbol_elf'] = DottConf.conf['bl_load_elf']
        if DottConf.conf['bl_symbol_elf'] is not None:
            if not os.path.exists(DottConf.conf['bl_symbol_elf']):
                raise ValueError(f'{DottConf.conf["bl_symbol_elf"]} does not exist.')
        log.info(f'BL ELF (symbol):       {DottConf.conf["bl_symbol_elf"]}')

        if 'bl_symbol_addr' not in DottConf.conf:
            DottConf.conf['bl_symbol_addr'] = 0x0
        elif 'bl_symbol_addr' == '':
            DottConf.conf['bl_symbol_addr'] = 0x0
        else:
            DottConf.conf['bl_symbol_addr'] = int(DottConf.conf['bl_symbol_addr'], base=16)
        log.info(f'BL ADDR (symbol):      0x{DottConf.conf["bl_symbol_addr"]:x}')

        if 'app_load_elf' not in DottConf.conf:
            raise Exception(f'app_load_elf not set')
        if not os.path.exists(DottConf.conf['app_load_elf']):
            raise ValueError(f'{DottConf.conf["app_load_elf"]} does not exist.')
        log.info(f'APP ELF (load):        {DottConf.conf["app_load_elf"]}')

        if 'app_symbol_elf' not in DottConf.conf:
            # if no symbol file is specified assume that symbols are contained in the load file
            DottConf.conf['app_symbol_elf'] = DottConf.conf['app_load_elf']
        if not os.path.exists(DottConf.conf['app_symbol_elf']):
            raise ValueError(f'{DottConf.conf["app_symbol_elf"]} does not exist.')
        log.info(f'APP ELF (symbol):      {DottConf.conf["app_symbol_elf"]}')

        if 'device_name' not in DottConf.conf:
            DottConf.conf["device_name"] = 'unknown'
        log.info(f'Device name:           {DottConf.conf["device_name"]}')

        if 'device_endianess' not in DottConf.conf:
            DottConf.conf['device_endianess'] = 'little'
        else:
            if DottConf.conf['device_endianess'] != 'little' and DottConf.conf['device_endianess'] != 'big':
                raise ValueError(f'device_endianess in {dott_ini} should be either "little" or "big".')
        log.info(f'Device endianess:      {DottConf.conf["device_endianess"]}')

        # determine J-Link path and version
        jlink_path, jlink_lib_name, jlink_version = DottConf._get_jlink_path(jlink_default_path, jlink_lib_name)
        DottConf.conf["jlink_path"] = jlink_path
        DottConf.conf["jlink_lib_name"] = jlink_lib_name
        DottConf.conf["jlink_version"] = jlink_version
        log.info(f'J-LINK local path:     {DottConf.conf["jlink_path"]}')
        log.info(f'J-LINK local version:  {DottConf.conf["jlink_version"]}')

        # We are connecting to a J-LINK gdb server which was not started by DOTT. Therefore it does not make sense
        # to print, e.g., SWD connection parameters.
        if 'jlink_interface' not in DottConf.conf:
            DottConf.conf['jlink_interface'] = 'SWD'
        log.info(f'J-LINK interface:      {DottConf.conf["jlink_interface"]}')

        if 'jlink_speed' not in DottConf.conf:
            DottConf.conf['jlink_speed'] = '15000'
        log.info(f'J-LINK speed (set):    {DottConf.conf["jlink_speed"]}')

        if 'jlink_serial' not in DottConf.conf:
            DottConf.conf['jlink_serial'] = None
        elif DottConf.conf['jlink_serial'] is not None and DottConf.conf['jlink_serial'].strip() == '':
            DottConf.conf['jlink_serial'] = None
        if DottConf.conf['jlink_serial'] is not None:
            log.info(f'J-LINK serial:         {DottConf.conf["jlink_serial"]}')

        if 'gdb_client_binary' not in DottConf.conf:
            default_gdb = 'arm-none-eabi-gdb-py'
            DottConf.conf['gdb_client_binary'] = str(Path(f'{os.environ["DOTTGDBPATH"]}/{default_gdb}'))
        log.info(f'GDB client binary:     {DottConf.conf["gdb_client_binary"]}')

        if 'gdb_server_addr' not in DottConf.conf:
            DottConf.conf['gdb_server_addr'] = None
        elif DottConf.conf['gdb_server_addr'].strip() == '':
            DottConf.conf['gdb_server_addr'] = None
        else:
            DottConf.conf['gdb_server_addr'] = DottConf.conf['gdb_server_addr'].strip()
        log.info(f'GDB server address:    {DottConf.conf["gdb_server_addr"]}')

        if 'gdb_server_port' not in DottConf.conf or DottConf.conf['gdb_server_port'] is None:
            DottConf.conf['gdb_server_port'] = '2331'
        elif DottConf.conf['gdb_server_port'].strip() == '':
            DottConf.conf['gdb_server_port'] = '2331'
        log.info(f'GDB server port:       {DottConf.conf["gdb_server_port"]}')

        if 'jlink_server_addr' not in DottConf.conf or DottConf.conf['jlink_server_addr'] is None:
            DottConf.conf['jlink_server_addr'] = None
        elif DottConf.conf['jlink_server_addr'].strip() == '':
            DottConf.conf['jlink_server_addr'] = None
        if DottConf.conf["jlink_server_addr"] != None:
            log.info(f'JLINK server address:  {DottConf.conf["jlink_server_addr"]}')

        if 'jlink_server_port' not in DottConf.conf or DottConf.conf['jlink_server_port'] is None:
            DottConf.conf['jlink_server_port'] = '19020'
        elif DottConf.conf['jlink_server_port'].strip() == '':
            DottConf.conf['jlink_server_port'] = '19020'
        if DottConf.conf["jlink_server_port"] != '19020':
            log.info(f'JLINK server port:     {DottConf.conf["jlink_server_port"]}')
        if DottConf.conf['gdb_server_addr'] is None:
            # no (remote) GDB server address given. try to find a local GDB server binary to launch instead

            if 'gdb_server_binary' in DottConf.conf:
                if not os.path.exists(DottConf.conf['gdb_server_binary']):
                    raise Exception(f'GDB server binary {DottConf.conf["gdb_server_binary"]} ({dott_ini}) not found!')
            elif os.path.exists(jlink_default_path):
                DottConf.conf['gdb_server_binary'] = str(Path(f'{jlink_path}/{jlink_gdb_server_binary}'))
            else:
                # As a last option we check if the GDB server binary is in PATH
                try:
                    subprocess.check_call((jlink_gdb_server_binary, '-device'))
                except subprocess.CalledProcessError:
                    # Segger gdb server exists and responded with an error since no device was specified
                    DottConf.conf['gdb_server_binary'] = jlink_gdb_server_binary
                except Exception as ex:
                    raise Exception(f'GDB server binary {jlink_gdb_server_binary} not found! Checked {dott_ini}, '
                                    'default location and PATH. Giving up.') from None
            log.info(f'GDB server binary:     {DottConf.conf["gdb_server_binary"]}')
        else:
            log.info('GDB server assumed to be already running (not started by DOTT).')
            DottConf.conf['gdb_server_binary'] = None

        default_mem_model: TargetMemModel = TargetMemModel.TESTHOOK
        if 'on_target_mem_model' not in DottConf.conf:
            DottConf.conf['on_target_mem_model'] = default_mem_model
        else:
            DottConf.conf['on_target_mem_model'] = str(DottConf.conf['on_target_mem_model']).upper()
            if DottConf.conf['on_target_mem_model'] not in TargetMemModel.get_keys():
                log.warn(f'On-target memory model ({DottConf.conf["on_target_mem_model"]}) from {dott_ini} is unknown. '
                         f'Falling back to default.')
                DottConf.conf['on_target_mem_model'] = default_mem_model
            else:
                DottConf.conf['on_target_mem_model'] = TargetMemModel[DottConf.conf['on_target_mem_model']]

        on_target_mem_prestack_alloc_size: int = 256
        if 'on_target_mem_prestack_alloc_size' in DottConf.conf:
            if str(DottConf.conf['on_target_mem_prestack_alloc_size']).strip() != '':
                on_target_mem_prestack_alloc_size = int(DottConf.conf['on_target_mem_prestack_alloc_size'])
        DottConf.conf['on_target_mem_prestack_alloc_size'] = on_target_mem_prestack_alloc_size

        on_target_mem_prestack_alloc_location: str = '_main_init'
        if 'on_target_mem_prestack_alloc_location' in DottConf.conf:
            if str(DottConf.conf['on_target_mem_prestack_alloc_location']).strip() != '':
                on_target_mem_prestack_alloc_location = str(DottConf.conf['on_target_mem_prestack_alloc_location'])
        DottConf.conf['on_target_mem_prestack_alloc_location'] = on_target_mem_prestack_alloc_location

        on_target_mem_prestack_halt_location: str = 'main'
        if 'on_target_mem_prestack_halt_location' in DottConf.conf:
            if str(DottConf.conf['on_target_mem_prestack_halt_location']).strip() != '':
                on_target_mem_prestack_halt_location = str(DottConf.conf['on_target_mem_prestack_halt_location'])
        DottConf.conf['on_target_mem_prestack_halt_location'] = on_target_mem_prestack_halt_location

        on_target_mem_prestack_total_stack_size: int = None
        if 'on_target_mem_prestack_total_stack_size' in DottConf.conf:
            if str(DottConf.conf['on_target_mem_prestack_total_stack_size']).strip() != '':
                on_target_mem_prestack_total_stack_size = int(DottConf.conf['on_target_mem_prestack_total_stack_size'])
        DottConf.conf['on_target_mem_prestack_total_stack_size'] = on_target_mem_prestack_total_stack_size

        if DottConf.conf['on_target_mem_model'] == TargetMemModel.PRESTACK:
            log.info(f'Std. target mem model for DOTT default fixtures:  {DottConf.conf["on_target_mem_model"]} '
                 f'({on_target_mem_prestack_alloc_size}bytes '
                 f'@{on_target_mem_prestack_alloc_location}; '
                 f'halt @{on_target_mem_prestack_halt_location}; '
                 f'total stack: {on_target_mem_prestack_total_stack_size if on_target_mem_prestack_total_stack_size is not None else "unknown"})')
        else:
            log.info(f'Std. target mem model for DOTT default fixtures:  {DottConf.conf["on_target_mem_model"]}')
