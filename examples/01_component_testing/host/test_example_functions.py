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
from dottmi.target_mem import TypedPtr
from dottmi.utils import DottConvert
from dottmi.dott import DottConf, dott
from dottmi.breakpoint import HaltPoint, InterceptPoint, InterceptPointCmds

class TestExampleFunctions(object):

    ##
    # \amsTestDesc Test function call without arguments.
    # \amsTestPrec None
    # \amsTestImpl Call target function which takes no arguments.
    # \amsTestResp Return value from target should have expected value.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0270
    def test_example_NoArgs(self, target_load, target_reset):
        res = dott().target.eval('example_NoArgs()')
        assert(42 == res)

    ##
    # \amsTestDesc Test function call without arguments where called function is static.
    # \amsTestPrec None
    # \amsTestImpl Call target function which takes no arguments.
    # \amsTestResp Return value from target should have expected value.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0270
    def test_example_NoArgsStatic(self, target_load, target_reset):
        res = dott().target.eval('example_NoArgsStatic()')
        assert(42 == res)

    ##
    # \amsTestDesc Test function call with two arguments.
    # \amsTestPrec None
    # \amsTestImpl Call target function which takes two arguments.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0270
    def test_example_Addition(self, target_load, target_reset):
        res = dott().target.eval('example_Addition(31, 11)')
        assert(42 == res)

    ##
    # \amsTestDesc Test function call with two pointer arguments.
    # \amsTestPrec None
    # \amsTestImpl Call target function which takes two pointer arguments.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionPtr(self, target_load, target_reset):
        dott().target.mem.alloc_type('uint32_t', val=9, var_name='$a')
        dott().target.mem.alloc_type('uint32_t', val=12, var_name='$b')
        res = dott().target.eval('example_AdditionPtr($a, $b)')
        assert(21 == res), 'Unexpected  return value'

    ##
    # \amsTestDesc Test function call with two pointer arguments. Use implementation variant without GDB convenience
    #              variables.
    # \amsTestPrec None
    # \amsTestImpl Call target function which takes two pointer arguments.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionPtr_Alternate(self, target_load, target_reset):
        dt = dott().target
        p_a = dt.mem.alloc_type('uint32_t', val=9)
        p_b = dt.mem.alloc_type('uint32_t', val=12)
        res = dt.eval(f'example_AdditionPtr({p_a}, {p_b})')
        assert(21 == res), 'Unexpected  return value'

    ##
    # \amsTestDesc Test function call with two pointer arguments. Use implementation variant without GDB convenience
    #              variables and array-based on-target memory allocation.
    # \amsTestPrec None
    # \amsTestImpl Call target function which takes two pointer arguments.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionPtr_AlternateArray(self, target_load, target_reset):
        dt = dott().target
        ptr = dt.mem.alloc_type('uint32_t', cnt=2)
        dt.eval(f'{ptr}[0] = 9')
        dt.eval(f'{ptr}[1] = 12')
        res = dt.eval(f'example_AdditionPtr(&{ptr}[0], &{ptr}[1])')
        assert(21 == res), 'Unexpected  return value'

    ##
    # \amsTestDesc Test function call with two pointer arguments. Also the return value shall be a pointer.
    # \amsTestPrec None
    # \amsTestImpl Call target function which takes two pointer arguments. Allocate memory also for the return
    #              value which is returned via a pointer.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionPtrRet(self, target_load, target_reset):
        dott().target.mem.alloc_type('uint32_t', val=10, var_name='$a')
        dott().target.mem.alloc_type('uint32_t', val=999, var_name='$b')
        dott().target.mem.alloc_type('uint32_t', val=0, var_name='$sum')
        res = dott().target.eval('example_AdditionPtrRet($a, $b, $sum)')
        my_sum = dott().target.eval('*$sum')
        assert(1009 == res), 'Unexpected return value'
        assert(1009 == my_sum), 'Unexpected return value'

    ##
    # \amsTestDesc Test function call with two pointer arguments. Also the return value shall be a pointer. Use
    #              implementation variant without GDB convenience variables.
    # \amsTestPrec None
    # \amsTestImpl Call target function which takes two pointer arguments. Allocate memory also for the return
    #              value which is returned via a pointer.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionPtrRet_Alternate(self, target_load, target_reset):
        dt = dott().target
        p_a = dt.mem.alloc_type('uint32_t', val=10)
        p_b = dt.mem.alloc_type('uint32_t', val=999)
        p_sum = dt.mem.alloc_type('uint32_t', val=0)
        res = dt.eval(f'example_AdditionPtrRet({p_a}, {p_b}, {p_sum})')
        my_sum = dt.eval(f'*{p_sum}')
        assert(1009 == res), 'Unexpected return value'
        assert(1009 == my_sum), 'Unexpected return value'

    ##
    # \amsTestDesc Test function call with a struct as argument.
    # \amsTestPrec None
    # \amsTestImpl Call target function with a struct argument. Allocate on-target memory for the struct.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionStruct(self, target_load, target_reset):
        dott().target.mem.alloc_type('my_add_t', var_name='$add_data')
        dott().target.eval('$add_data->a = 55')
        dott().target.eval('$add_data->b = 22')
        dott().target.eval('$add_data->sum = 0')
        res = dott().target.eval('example_AdditionStruct(*$add_data)')
        assert(77 == res), 'Unexpected return value'

    ##
    # \amsTestDesc Test function call with a struct as argument. Use implementation variant without GDB convenience
    #              variables.
    # \amsTestPrec None
    # \amsTestImpl Call target function with a struct argument. Allocate on-target memory for the struct.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionStruct_Alternate(self, target_load, target_reset):
        dt = dott().target
        p_dat = dt.mem.alloc_type('my_add_t')
        dt.eval(f'{p_dat}->a = 55')
        dt.eval(f'{p_dat}->b = 22')
        dt.eval(f'{p_dat}->sum = 0')
        res = dt.eval(f'example_AdditionStruct(*{p_dat})')
        assert(77 == res), 'Unexpected return value'

    ##
    # \amsTestDesc Test ctypes-based declaration and initialization of target struct. The target struct is replicated
    #              on the host using ctypes and then bulk-copied to the target using mem write. This significantly
    #              reduces the time for on-target struct initialization.
    # \amsTestPrec None
    # \amsTestImpl Create a ctypes struct matching the on-target struct. Fill the ctypes struct on the host and copy
    #              it in a bulk transfer to the target. Call the addition function taking the struct as an argument.
    # \amsTestResp Result of addition shall be the sum of the two operands.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionStruct_ctypes(self, target_load, target_reset):
        import ctypes

        # Arm Compiler Struct Packing notes: https://developer.arm.com/docs/100748/latest/writing-optimized-code/packing-data-structures
        # see ctypes _pack_ attribute

        class my_add_t(ctypes.LittleEndianStructure):
            _pack_ = 0
            _fields_ = [('paddA', ctypes.c_uint8),
                        ('a', ctypes.c_uint32),
                        ('paddB', ctypes.c_uint8),
                        ('b', ctypes.c_uint32),
                        ('paddC', ctypes.c_uint8),
                        ('sum', ctypes.c_uint32)
                        ]

        p_dat = dott().target.mem.alloc_type('my_add_t')
        my = my_add_t(paddA=0, a=22, paddB=0, b=55, paddC=0, sum=0)
        dott().target.mem.write(p_dat, bytes(my))

        res = dott().target.eval(f'example_AdditionStruct(*{p_dat})')
        assert(77 == res), 'Unexpected return value'

    ##
    # \amsTestDesc Test function call with a struct pointer as argument.
    # \amsTestPrec None
    # \amsTestImpl Call target function with a struct argument. Allocate on-target memory for the struct.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionStructPtr(self, target_load, target_reset):
        dott().target.mem.alloc_type('my_add_t', var_name='$add_data')
        dott().target.eval('$add_data->a = 55')
        dott().target.eval('$add_data->b = 22')
        dott().target.eval('$add_data->sum = 0')
        res = dott().target.eval('example_AdditionStructPtr($add_data)')
        my_sum = dott().target.eval('$add_data->sum')
        assert(77 == res), 'Unexpected return value'
        assert(77 == my_sum), 'Unexpected return value'

    ##
    # \amsTestDesc Test function call with a struct pointer as argument. Use implementation variant without GDB
    #              convenience variables.
    # \amsTestPrec None
    # \amsTestImpl Call target function with a struct argument. Allocate on-target memory for the struct.
    # \amsTestResp Return value should be the sum of the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0260, RS_0270
    def test_example_AdditionStructPtr_Alternate(self, target_load, target_reset):
        dt = dott().target
        p_dat = dt.mem.alloc_type('my_add_t')
        dt.eval(f'{p_dat}->a = 55')
        dt.eval(f'{p_dat}->b = 22')
        dt.eval(f'{p_dat}->sum = 0')
        res = dt.eval(f'example_AdditionStructPtr({p_dat})')
        my_sum = dt.eval(f'{p_dat}->sum')
        assert(77 == res), 'Unexpected return value'
        assert(77 == my_sum), 'Unexpected return value'

    ##
    # \amsTestDesc Test function call with many args (i.e., more args than are passed via registers).
    # \amsTestPrec None
    # \amsTestImpl Call target function which takes 6 arguments.
    # \amsTestResp Return value should be the sum of the arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0270
    def test_example_ManyArgs(self, target_load, target_reset):
        args = (11, 12, 13, 14, 15, 16)
        res = dott().target.eval('example_ManyArgs(%d, %d, %d, %d, %d, %d)' % args)
        assert(sum(args) == res)

    ##
    # \amsTestDesc Test function which takes a function pointer and two scalars as arguments and calls this function.
    # \amsTestPrec None
    # \amsTestImpl Call target function with a function pointer argument and two scalars.
    # \amsTestResp Return value should be the sum or difference (depending on the passed function pointer) of
    #              the two provided arguments.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0270
    def test_example_CustomOperation(self, target_load, target_reset):
        args = (44, 22)
        exp_diff = args[0] - args[1]
        exp_sum = sum(args)

        func_sub_ptr = dott().target.eval('&example_FunctorSub')
        res = dott().target.eval(f'example_CustomOperation({func_sub_ptr}, {args[0]}, {args[1]})')
        assert(exp_diff == res), f'expected: {exp_diff}, is: {res}'

        func_add_ptr = dott().target.eval('&example_FunctorAdd')
        res = dott().target.eval(f'example_CustomOperation({func_add_ptr}, {args[0]}, {args[1]})')
        assert(exp_sum == res), f'expected: {exp_sum}, is: {res}'

    ##
    # \amsTestDesc Test function which takes a string as argument and returns the string's length.
    # \amsTestPrec None
    # \amsTestImpl Call target function with a string as argument.
    # \amsTestResp Return value should be the length of the provided string.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0270
    def test_example_ArgString(self, target_load, target_reset):
        msg = 'Sensing is life.\0'
        addr = dott().target.mem.alloc_type('char', cnt=len(msg), val=0x0)
        dott().target.mem.write(addr, msg.encode(encoding='ascii'))
        res = dott().target.eval(f'example_StringLen({addr})')
        assert(len(msg) - 1 == res), f'expected: {len(msg)}, is: {res}'

        # same as above but with direct setting of initial data
        addr = dott().target.mem.alloc_type('char', cnt=len(msg), val=msg)
        res = dott().target.eval(f'example_StringLen({addr})')
        assert(len(msg) - 1 == res), f'expected: {len(msg)}, is: {res}'

    ##
    # \amsTestDesc Test function which takes an integer array as argument and returns the sum of the elements.
    # \amsTestPrec None
    # \amsTestImpl Call target function with a integer array as argument.
    # \amsTestResp Return value should be the sum of the array elements.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0270
    def test_example_SumElements(self, target_load, target_reset):
        dt = dott().target

        elements = [0, 1, 2, 65535, 99]

        elements_bytes = DottConvert.uint16_to_bytes(elements)
        p: TypedPtr = dt.mem.alloc_type('uint16_t', cnt=len(elements), val=0x0)
        dt.mem.write(p, bytes(elements_bytes))

        res = dt.eval(f'example_SumElements({p}, {len(elements)})')
        assert (sum(elements) == res), f'expected: {sum(elements)}, is: {res}'

        # update some elements. note: index notation also works for on-target memory (arrays)
        elements[0] = 128
        elements[3] = 99
        p[0] = elements[0]
        p[3] = elements[3]

        res = dt.eval(f'example_SumElements({p}, {len(elements)})')
        assert (sum(elements) == res), f'expected: {sum(elements)}, is: {res}'

    ##
    # \amsTestDesc Test function itself calls two sub functions, adds the results of the sub functions and returns this
    #              result.
    # \amsTestPrec None
    # \amsTestImpl Call target function which calls two sub functions.
    # \amsTestResp Return value should be the sum of the two values returned by the sub functions.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0270
    def test_example_AdditionSubcalls(self, target_load, target_reset):
        res = dott().target.eval('example_AdditionSubcalls()')
        assert(63 == res)

    ##
    # \amsTestDesc Test function itself calls two sub functions, adds the results of the sub functions and returns this
    #              result. Intercept the calls to the sub-functions and inject user-defined data.
    # \amsTestPrec None
    # \amsTestImpl Call target function which calls two sub functions. Define intercept points for the two sub functions
    #              and inject user-defined data.
    # \amsTestResp Return value should be the sum of the two injected values.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0250, RS_0270
    def test_example_AdditionSubcallsBasicIntercept(self, target_load, target_reset):
        bp_a = InterceptPointCmds('example_GetA', ['return 10'])
        bp_b = InterceptPointCmds('example_GetB', ['set var *b = 99',
                                                   'return 0'])
        res = dott().target.eval('example_AdditionSubcalls()')

        bp_a.delete()
        bp_b.delete()

        assert(109 == res)

    ##
    # \amsTestDesc Test function itself calls two sub functions, adds the results of the sub functions and returns this
    #              result. Intercept the calls to the sub-functions and inject user-defined data. This time use fully
    #              featured intercept points (i.e., implement the reached method).
    # \amsTestPrec None
    # \amsTestImpl Call target function which calls two sub functions. Define intercept points for the two sub functions
    #              and inject user-defined data.
    # \amsTestResp Return value should be the sum of the two injected values.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0250, RS_0270
    def test_example_AdditionSubcallsExtIntercept(self, target_load, target_reset):

        class IpA(InterceptPoint):
            def reached(self):
                self.ret(10)

        class IpB(InterceptPoint):
            def reached(self):
                self.eval('*b = 89')
                self.eval('*b += 10')
                val = self.eval('*b')
                assert(val == 99)
                self.ret(0)

        ipa = IpA('example_GetA')
        ipb = IpB('example_GetB')

        res = dott().target.eval('example_AdditionSubcalls()')

        ipa.delete()
        ipb.delete()

        assert(109 == res)

    ##
    # \amsTestDesc Test if global data variables are properly initialized.
    # \amsTestPrec None
    # \amsTestImpl Halt the target in the ResetHandler, write a well known pattern into a global variable, let the
    #              target continue to main and check if the variable was properly initialized.
    # \amsTestResp Variable shall no longer hold the well known pattern but its initialization value.
    # \amsTestType Component
    # \amsTestReqs RS_0110, RS_0230, RS_0240, RS_0270
    def test_global_data_access(self, target_load, target_reset):
        # set breakpoints before the data section gets initialized (Reset_Handler) and after (main)
        bp_reset_handler = HaltPoint('Reset_Handler')
        bp_main = HaltPoint('main')
        dott().target.reset()

        # if execution is SRAM-based, we need to manually tweak the SP and PC after the reset
        if DottConf.conf['exec_type'] == 'SRAM':
            dott().target.eval('$sp = *(0x20000000)')
            dott().target.eval('$pc = *(0x20000004)')

        dott().target.cont()

        # set the content of the global_data variable (located in RW data) to known pattern and let target continue
        bp_reset_handler.wait_complete()
        dott().target.eval('global_data = 0xaabbaabb')
        assert(hex(dott().target.eval('global_data')) == '0xaabbaabb')
        dott().target.cont()

        # check if global data was properly initialized by the scatter loader
        bp_main.wait_complete()
        assert(hex(dott().target.eval('global_data')) == '0xdeadbeef')
