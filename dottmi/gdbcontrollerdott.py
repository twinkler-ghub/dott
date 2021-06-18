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

import logging

from pygdbmi.gdbcontroller import GdbController, DEFAULT_TIME_TO_CHECK_FOR_ADDITIONAL_OUTPUT_SEC


# The IoManager.py from pygdbmi uses the global logger for debug output. We suppress it with a filter.
class LogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> int:
        if record.filename == 'IoManager.py':
            return False
        return True


class GdbControllerDott(GdbController):
    def __init__(self, command,
                 time_to_check_for_additional_output_sec=DEFAULT_TIME_TO_CHECK_FOR_ADDITIONAL_OUTPUT_SEC):

        # set logging filter for pygdbmi
        logging.getLogger().addFilter(LogFilter())
        super().__init__(command, time_to_check_for_additional_output_sec)
