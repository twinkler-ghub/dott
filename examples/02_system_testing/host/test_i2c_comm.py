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

from dottmi.breakpoint import HaltPoint, InterceptPoint
from dottmi.dott import dott
from dottmi.utils import DOTT_LABEL, DottConvert


class TestI2cCommunication(object):

    ##
    # \amsTestDesc This test checks if the command id (first byte of data packet) is correctly received by the target.
    # \amsTestPrec None
    # \amsTestImpl Send command to target, halt target at defined location and read back the command id.
    # \amsTestResp Command id received by the target shall match the one sent by the host.
    # \amsTestType System
    # \amsTestReqs RS_0220, RS_0110, RS_0400, RS_0410
    def test_RegWriteRead(self, target_load, target_reset, i2c_comm):
        bp = HaltPoint(DOTT_LABEL('I2C_READ_DONE'))
        dott().target.cont()

        i2c_comm.pi.i2c_write_device(i2c_comm.dev, [0x99, *([0x0] * 8)])

        bp.wait_complete()
        assert(0x99 == dott().target.eval('_data[0]')), 'Command byte not correctly received by target'

        dott().target.cont()
        i2c_comm.pi.i2c_write_device(i2c_comm.dev, [0x77, *([0x0] * 8)])

        bp.wait_complete()
        assert(0x77 == dott().target.eval('_data[0]')), 'Command byte not correctly received by target'

    ##
    # \amsTestDesc This test sends a command to the target via I2C and checks if it triggers the expected action on
    #              the target (an addition of the parameters provided as part of the command package).
    # \amsTestPrec None
    # \amsTestImpl Send command packet (including arguments for addition) to target. Halt the target at a defined
    #              location (after the command was executed) and check the outcome. In addition check that data
    #              deserialization from byte array on target matches the serialization behavior on the host.
    # \amsTestResp Addition result on target shall match the expected one.
    # \amsTestType System
    # \amsTestReqs RS_0220, RS_0110, RS_0400, RS_0410
    def test_CmdAdd(self, target_load, target_reset, i2c_comm):
        hp = HaltPoint(DOTT_LABEL('CMD_ADD_EXIT'))

        a = 78231231
        b = 12345678
        a_bytes = DottConvert.uint32_to_bytes(a)
        b_bytes = DottConvert.uint32_to_bytes(b)

        dott().target.cont()
        i2c_comm.pi.i2c_write_device(i2c_comm.dev, [0x10, *a_bytes, *b_bytes])

        hp.wait_complete(timeout=4)
        deser_a = dott().target.eval('a')
        deser_b = dott().target.eval('b')
        assert (a == deser_a), 'deserialized data on target does not match sent data'
        assert (b == deser_b), 'deserialized data on target does not match sent data'

        sum = dott().target.eval('sum')
        assert ((a + b) == sum), 'sum does not match expected value'

    ##
    # \amsTestDesc This test checks if a certain label (error handling code) is reached if an unknown (unsupported)
    #              command is sent to the target via I2C.
    # \amsTestPrec None
    # \amsTestImpl Send an unsupported command code (0xff) to the target and check that it reaches the error handling
    #              code for unknown commands.
    # \amsTestResp Error handling code for unknown commands is reached.
    # \amsTestType System
    # \amsTestReqs RS_0220, RS_0110, RS_0400, RS_0410
    def test_CmdUnknown(self, target_load, target_reset, i2c_comm):
        hp = HaltPoint(DOTT_LABEL('UNKNOWN_CMD'))

        dummy = DottConvert.uint32_to_bytes(0)

        dott().target.cont()
        i2c_comm.pi.i2c_write_device(i2c_comm.dev, [0xff, *dummy, *dummy])

        try:
            hp.wait_complete(timeout=4)
        except TimeoutError:
            assert False, 'Command not detected as unknown command.'

    ##
    # \amsTestDesc This test checks if a certain label (error handling code) is reached if a valid command is send via
    #              I2C which is then on-the-fly replaced with an invalid command using a DOTT intercept point.
    # \amsTestPrec None
    # \amsTestImpl Send a valid command via I2C, inject a faulty command in the interrupt handler callback and check
    #              tat the error handling code is reached for faulty command.
    # \amsTestResp Error handling code for unknown commands is reached.
    # \amsTestType System
    # \amsTestReqs RS_0220, RS_0110, RS_0400, RS_0410
    def test_CmdInjectUnknown(self, target_load, target_reset, i2c_comm):
        hp = HaltPoint(DOTT_LABEL('UNKNOWN_CMD'))

        class MyIp(InterceptPoint):
            def reached(self):
                self.eval('_recv_buf[0] = 0xff')

        ip = MyIp('HAL_I2C_SlaveRxCpltCallback')

        a = 78231231
        b = 12345678
        a_bytes = DottConvert.uint32_to_bytes(a)
        b_bytes = DottConvert.uint32_to_bytes(b)

        dott().target.cont()
        i2c_comm.pi.i2c_write_device(i2c_comm.dev, [0x10, *a_bytes, *b_bytes])

        try:
            hp.wait_complete(timeout=4)
        except TimeoutError:
            assert False, 'Command not detected as unknown command.'
