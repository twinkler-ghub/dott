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

import ctypes
import time

from dottmi.utils import log
from dottmi.dott import dott
from dottmi.breakpoint import HaltPoint, InterceptPoint, InterceptPointCmds


class TestTemplate(object):

    ##
    # \amsTestDesc This test checks a global counter variable is properly incremented by the main loop.
    # \amsTestPrec None
    # \amsTestImpl Let target run for some time.
    # \amsTestResp Counter variable is not zero anymore.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0120
    def test_load(self, target_load, target_reset):
        assert (0 == dott().target.eval('global_data')), 'counter should initially be zero'
        dott().target.cont()
        time.sleep(.5)
        dott().target.halt()
        assert (0 < dott().target.eval('global_data')), 'counter should be greater than zero'
