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

from dottmi.dott import DottConf
from dottmi.fixtures import target_load_flash, target_load_sram, target_reset_flash, target_reset_sram

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
DottConf.conf['app_load_elf'] = f'01_component_testing/target/build/dott_example_01{postfix}/dott_example_01{postfix}.bin.elf'
DottConf.conf['app_symbol_elf'] = f'01_component_testing/target/build/dott_example_01{postfix}/dott_example_01{postfix}.axf'

# re-target target_reset/load fixtures
if postfix != '':
    target_load = target_load_sram
    target_reset = target_reset_sram
else:
    target_load = target_load_flash
    target_reset = target_reset_flash
