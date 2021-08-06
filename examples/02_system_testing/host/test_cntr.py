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

import time
from typing import List, Tuple


import pytest
from matplotlib import pyplot

from dottmi.breakpoint import HaltPoint, InterceptPoint
from dottmi.dott import dott
from dottmi.pylinkdott import TargetDirect
from dottmi.utils import DOTT_LABEL


class TestCounters(object):
    ##
    # \amsTestDesc This test checks if the Systick counter advances over time (and hence if the Systick interrupt
    #              fires).
    # \amsTestPrec None
    # \amsTestImpl Let target run for some time.
    # \amsTestResp Systick counter shall be zero initially and shall have advanced while target was running.
    # \amsTestType System
    # \amsTestReqs RS_0110, RS_0280
    def test_SystickRunning(self, target_load, target_reset):
        assert (0 == dott().target.eval('_tick_cnt')), 'Systick count shall initially be zero.'
        dott().target.cont()
        time.sleep(2.5)
        dott().target.halt()
        assert (2000 <= dott().target.eval('_tick_cnt')), 'Systick counter should have advanced while target was running'

    ##
    # \amsTestDesc This test checks if the Systick counter advances over time. In contrast to the previous test it
    #              uses the live access feature to read the current value of the Systick counter without halting the
    #              target.
    # \amsTestPrec None
    # \amsTestImpl Let target run for some time and periodically sample tick count while target is running.
    # \amsTestResp Systick counter shall be zero initially and shall have advanced while target was running.
    # \amsTestType System
    # \amsTestReqs RS_0110, RS_0280
    @pytest.mark.live_access
    def test_SystickRunningLive(self, target_load, target_reset, live_access):
        cnt_addr = dott().target.eval('&_tick_cnt')
        cnt_last = dott().target.eval('_tick_cnt')
        assert (0 == cnt_last), 'Systick count shall initially be zero.'
        dott().target.cont()

        for i in range(10):
            time.sleep(.5)
            cnt = live_access.mem_read_32(cnt_addr)
            assert (cnt > cnt_last), 'Systick counter should have advanced'
            cnt_last = cnt

    ##
    # \amsTestDesc This test demonstrates to live-access the systick counter of the running target and plot the
    #              acquired values into a png file.
    # \amsTestPrec None
    # \amsTestImpl Let target boot, continue execution and perform live access to the target's systick counter.
    # \amsTestResp None - this is a demonstration test.
    # \amsTestType System
    # \amsTestReqs RS_0110, RS_0280
    @pytest.mark.live_access
    def test_SystickSampleLive(self, target_load, target_reset, live_access):
        def sample_mem_addr(mem_addr: int, duration: float, live: TargetDirect, plot_live: bool = False) -> Tuple[List[float], List[int]]:
            duration_list: List[float] = []
            samples_list: List[int] = []
            time_start = time.time()
            while (time.time() - time_start) < duration:
                duration_list.append(time.time() - time_start)
                samples_list.append(live.mem_read_32(mem_addr))
                if plot_live:
                    pyplot.ylabel('systick')
                    pyplot.xlabel('host runtime')
                    pyplot.plot(duration_list, samples_list)
                    pyplot.draw()
                    pyplot.pause(0.0001)
                    pyplot.clf()

            return duration_list, samples_list

        dott().target.cont()

        addr = dott().target.eval('&_tick_cnt')
        (host_time, msecs_samples) = sample_mem_addr(addr, 1.0, live_access, plot_live=False)

        dott().target.halt()

        # plot the data samples from the target
        pyplot.clf()
        pyplot.plot(host_time, msecs_samples)
        pyplot.ylabel('systick')
        pyplot.xlabel('host runtime')
        pyplot.savefig('test_systick_sample_live', dpi=200)

    ##
    # \amsTestDesc This test checks if the timer counter for timer 7 (TIM7) advances.
    # \amsTestPrec None
    # \amsTestImpl Let target run for some time.
    # \amsTestResp Timer counter shall be larger than zero after this time period.
    # \amsTestType System
    # \amsTestReqs RS_0110, RS_0290, RS_0280
    def test_TimerRunning(self, target_load, target_reset):
        assert (0 == dott().target.eval('_timer_cnt')), 'Timer count shall initially be zero.'
        dott().target.cont()
        time.sleep(1)
        dott().target.halt()
        assert (0 < dott().target.eval('_timer_cnt')), 'Timer count should have advanced while target was running'

    ##
    # \amsTestDesc This test demonstrates who a timer interrupt can be generated 'manually' via DOTT which, in some
    #              situations, might be a useful approach to test correct interrupt handling in firmware.
    #              In addition an InterceptPoint is set in the interrupt handler and the timer counter is altered
    #              in the InterceptPoint. Before generating the next interrupt, the test waits until the InterceptPoint
    #              is completed.
    # \amsTestPrec None
    # \amsTestImpl Set an InterceptPoint in the timer's interrupt handler and increment the timer counter.
    #              Let target boot, then disable the clock for timer 7 (TIM7) such that its interrupt does not fire
    #              anymore. Reset the timer 7 counter variable to 0 and ensure that it does not increase anymore. Next,
    #              let the target run again and manually set the timer 7 interrupt pending via target live access. Wait
    #              for completion of the intercept point and set the next interrupt pending.
    # \amsTestResp The timer counter shall be twice the number of times the timer 7 interrupt was set pending manually.
    # \amsTestType System
    # \amsTestReqs RS_0110, RS_0280, RS_0290, RS_0300
    @pytest.mark.irq_testing
    @pytest.mark.live_access
    def test_TimerManualIrqAdvanced(self, target_load, target_reset, live_access):
        APB1ENR = 0x4002101c  # APB1 enable register
        ISPR = 0xE000E200  # interrupt set pending register

        # wait until the target has reached function app_main
        hp = HaltPoint('app_main')
        dott().target.cont()
        hp.wait_complete()
        hp.delete()

        # Custom InterceptPoint which performs an additional counter increment.
        class MyIp(InterceptPoint):
            def reached(self):
                self.eval('_timer_cnt++')

        ip_tmr = MyIp(DOTT_LABEL('TIM7_IRQHandler_End'))

        # disable the clock for TIM7 such that it does not fire anymore and reset the timer counter to zero
        dott().target.eval(f'*{APB1ENR} &= ~0x20')
        dott().target.eval('_timer_cnt = 0')

        # let target run and ensure that the timer counter is still zero
        dott().target.cont()
        time.sleep(1)
        dott().target.halt()
        timer_cnt = dott().target.eval('_timer_cnt')
        assert(0 == timer_cnt), 'Expected timer count to be 0'

        # let target run again and via live target access set the TIM7 interrupt pending 4 times (i.e., 'manually'
        # trigger the TIM7 interrupt)
        dott().target.cont()
        for i in range(4):
            live_access.mem_write_32(ISPR, [0x000040000])
            ip_tmr.wait_complete()

        # halt target and check that timer count actually is 8 (interrupt was raised 4 times but our intercept point
        # does an additional increment for _timer_cnt for each interrupt and hence the timer count should be 8)
        dott().target.halt()
        timer_cnt = dott().target.eval('_timer_cnt')
        assert(8 == timer_cnt), 'Expected timer count to be 8'

    ##
    # \amsTestDesc This test checks if dott().target.ret() (without return value) works as intended.
    # \amsTestPrec None
    # \amsTestImpl Let target halt when entering a function and return from the function. Any side effects normally
    #              caused by the function (e.g., altering a module variable) can not be observed.
    # \amsTestResp Function side effects (alteration of module variable) can not be observed when returning early.
    # \amsTestType System
    # \amsTestReqs artf77204
    def test_return(self, target_load, target_reset):
        dt = dott().target

        hp_before = HaltPoint(DOTT_LABEL('BEFORE_ALTER_MY_VAL'))
        hp_alter = HaltPoint('alter_my_val')
        hp_after = HaltPoint(DOTT_LABEL('AFTER_ALTER_MY_VAL'))

        dt.cont()
        hp_before.wait_complete()
        assert dt.eval('_my_val') == 0

        dt.cont()
        hp_alter.wait_complete()
        dt.ret()
        assert dt.eval('_my_val') == 0

        dt.cont()
        hp_after.wait_complete()
        assert dt.eval('_my_val') == 0

        dt.reset()

        dt.cont()
        hp_before.wait_complete()
        assert dt.eval('_my_val') == 0

        dt.cont()
        hp_alter.wait_complete()
        assert dt.eval('_my_val') == 0

        dt.cont()
        hp_after.wait_complete()
        assert dt.eval('_my_val') == 0xffaa5500
