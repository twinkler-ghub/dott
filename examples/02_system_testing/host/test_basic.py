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

from dottmi.breakpoint import HaltPoint
from dottmi.dott import dott
from dottmi.utils import DOTT_LABEL


class TestBasic(object):

    ##
    # \amsTestDesc This test checks if dott().target.ret() (without return value) works as intended.
    # \amsTestPrec None
    # \amsTestImpl Let target halt when entering a function and return from the function. Any side effects normally
    #              caused by the function (e.g., altering a module variable) can not be observed.
    # \amsTestResp Function side effects (alteration of module variable) can not be observed when returning early.
    # \amsTestType System
    # \amsTestReqs artf77204
    def test_ReturnWithoutArguments(self, target_load, target_reset):
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
