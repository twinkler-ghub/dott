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

from . conftest import target_reset_sram_stm32f072
from dottmi.breakpoint import HaltPoint
from dottmi.dott import DottConf, dott


class TestSystemInit(object):

    ##
    # \amsTestDesc Test if a variable located in the BSS section is actually zero-initialized by the compiler's runtime
    #              before control is passed to main.
    # \amsTestPrec None
    # \amsTestImpl Add breakpoints to Reset_Handler and main. Reset the target, wait unit the Reset_Handler is reached.
    #              Write a non-zero pattern into a variable located in BSS section. Let target run until main is reached
    #              and check that variable in BSS section has been zeroed out.
    # \amsTestResp Variable in BSS section is zeroed out by compiler's runtime.
    # \amsTestType System
    # \amsTestReqs RS_0110
    def test_sysinit_bss_section(self, target_load, target_reset):
        # when entering the test the target is halted at the DOTT test hook

        # create halt points in Reset_Handler and main
        hp_reset = HaltPoint('Reset_Handler')
        hp_main = HaltPoint('main')

        # reset the target
        dott().target.reset()

        # if execution is SRAM-based, we need to manually tweak the SP and PC after the reset
        if DottConf.conf['exec_type'] == 'SRAM':
            dott().target.eval('$sp = *(0x20000000)')
            dott().target.eval('$pc = *(0x20000004)')

        # let target run and wait until it has reached the reset handler
        dott().target.cont()
        hp_reset.wait_complete()

        # write some well known, non-zero pattern int a variable located in the BSS section
        pattern = 0xaabbaabb
        dott().target.eval(f'_sample_cnt = {pattern}')
        assert (pattern == dott().target.eval('_sample_cnt')), 'expected to read back test pattern'

        # continue and wait until main has been reached; the variable in bss shall now be zero
        dott().target.cont()
        hp_main.wait_complete()
        assert (0x0 == dott().target.eval('_sample_cnt')), 'expected to read back zero'

    ##
    # \amsTestDesc Test if a variable located in the RW DATA section is properly initialized (i.e., if data is properly
    #              copied from FLASH to RAM) by the compiler's runtime before control is passed to main.
    # \amsTestPrec None
    # \amsTestImpl Add breakpoints to Reset_Handler and main. Reset the target, wait unit the Reset_Handler is reached.
    #              Zero out a variable located in RW DATA section. Let target run until main is reached
    #              and check that variable in DATA section has been initialized.
    # \amsTestResp Variable in DATA section is initialized by compiler's runtime.
    # \amsTestType System
    # \amsTestReqs RS_0110
    def test_sysinit_data_section(self, target_load, target_reset):
        # when entering the test the target is halted at the DOTT test hook

        # create halt points in Reset_Handler and main
        hp_reset = HaltPoint('Reset_Handler')
        hp_main = HaltPoint('main')

        # reset the target
        dott().target.reset()

        # if execution is SRAM-based, we need to manually tweak the SP and PC after the reset
        if DottConf.conf['exec_type'] == 'SRAM':
            dott().target.eval('$sp = *(0x20000000)')
            dott().target.eval('$pc = *(0x20000004)')

        # let target run and wait until it has reached the reset handler
        dott().target.cont()
        hp_reset.wait_complete()

        # write some well known, non-zero pattern int a variable located in the BSS section
        dott().target.eval('_test_data = 0x0')
        assert (0x0 == dott().target.eval('_test_data')), 'expected to read back 0x0'

        # continue and wait until main has been reached; the variable in bss shall now be zero
        dott().target.cont()
        hp_main.wait_complete()
        assert (0xdeadbeef == dott().target.eval('_test_data')), 'expected to read back 0xdeadbeef'

