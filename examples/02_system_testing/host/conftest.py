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

import pytest

from dottmi.dott import DottConf, dott
from dottmi.fixtures import target_reset_common, target_load_flash, target_load_sram, target_reset_flash

# check if the DOTT_RUN_SRAM environment variable is 'yes'; if so execute the tests with the SRAM-based binary.
postfix = ''
DottConf.conf['exec_type'] = 'FLASH'
try:
    val = os.environ['DOTT_RUN_SRAM']
    if val.lower() == 'yes':
        postfix = '_sram'
        DottConf.conf['exec_type'] = 'SRAM'
except:
    pass

# set binaries used for the tests in this folder (relative to main conftest file)
DottConf.conf['app_load_elf'] = f'02_system_testing/target/build/dott_example_02{postfix}/dott_example_02{postfix}.bin.elf'
DottConf.conf['app_symbol_elf'] = f'02_system_testing/target/build/dott_example_02{postfix}/dott_example_02{postfix}.axf'


def setup_cb() -> None:
    """
    This callback function is called right after reset. It enables the memory remapping of the SRAM of the Cortex-M0
    (STM32F072 used as reference system) to address 0x0. This is required when running code from SRAM which requires the
    (SRAM) vector table to be located at address 0x0.

    Returns:
        None.
    """
    SYSCFG_CFGR1 = 0x40010000
    dott().target.eval(f'*{SYSCFG_CFGR1} |= 0x3')


@pytest.fixture(scope='function')
def target_reset_sram_stm32f072(request) -> None:
    """
    This is a specialized reset fixture for the STM32F072 Cortex-M0 (DOTT reference system) which performs system
    reset and re-maps the SRAM to address 0 (using the setup_cb function above).
    Args:
        request: Request from pytest.

    Returns:
        None.
    """
    yield from target_reset_common(request, sp='0x20000000', pc='0x20000004', setup_cb=setup_cb)


# re-target target_reset/load fixtures
if postfix != '':
    # callback function for early device initialization
    target_load = target_load_sram
    target_reset = target_reset_sram_stm32f072
else:
    target_load = target_load_flash
    target_reset = target_reset_flash


def pytest_configure(config):
    # register markers with pytest
    config.addinivalue_line("markers", "live_access: marker for tests which access the target while it is running")
    config.addinivalue_line("markers", "irq_testing: marker for tests which 'manually' "
                                       "generate interrupts for testing purposes")
