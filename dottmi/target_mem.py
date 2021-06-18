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

import binascii
import math
import struct
from enum import Enum
from typing import Union, Dict

from dottmi.dottexceptions import DottException
from dottmi.utils import log

ALIGN_DEFAULT = 4  # default alignment for memory allocation is 4 bytes


class TargetMemModel(Enum):
    """
    Enum for the different on-target memory allocation models supported by DOTT.
    """
    NOALLOC  = 0x0  # Don't use any of the built-in on-target memory allocation models.
    TESTHOOK = 0x1  # DOTT test-hook based memory allocation
    PRESTACK = 0x2  # memory allocation prior to stack memory ('stack stealing')

    @classmethod
    def get_keys(cls):
        return list(map(lambda c: c.name, cls))


# -------------------------------------------------------------------------------------------------
class TypedPtr:
    def __init__(self, target: 'Target', addr: int, var_type: str = None) -> None:
        """
        Constructor.

        Args:
            target: Target instance.
            addr: Address represented by the pointer.
            var_type: Type of the variable the pointer is pointing to.
        """
        self._target: 'Target' = target
        self._addr: int = addr
        self._var_type: str = var_type
        if self._var_type is None:
            self._var_type = 'void'

    @property
    def type(self) -> str:
        """
        This function returns the they of the variable the pointer is pointing to.

        Returns:
            Returns the type of the variable the pointer is pointing to.
        """
        return self._var_type

    @property
    def addr(self) -> int:
        """
        This function returns the raw address.

        Returns:
            Returns raw address as integer.
        """
        return self._addr

    @property
    def val(self) -> Union[int, float, bool, str, None]:
        """
        This function dereferences the pointer and returns the value. This might not be possible for all data types
        (e.g., composite types).

        Returns:
            Dereferences the pointer and returns the value.
        """
        return self._target.eval(f'*({self.__str__()})')

    def __str__(self) -> str:
        """
        This function returns a string containing address in hex (pre-fixed with 0x) together with the type of
        the pointer as a prefix. E.g., (uint32_t*)0x20000000

        Returns:
            Returns string representation of the pointer in hex format together with type prefix.
        """
        return f'(({self._var_type}*)0x{self._addr:x})'


# -------------------------------------------------------------------------------------------------
class TargetMem(object):
    def __init__(self, target: 'Target', target_mem_start_addr: int, target_mem_num_bytes: int, zero_mem: bool = True):
        """
        Constructor.

        Args:
            target: The target instance.
            target_mem_start_addr: The memory address where DOTT's on-target scratchpad memory starts.
            target_mem_num_bytes: The size in bytes of DOTT's on-target scratchpad memory.
            zero_mem: Zero out the on-target scratchpad memory when calling reset (default: True).
        """
        self._target: 'Target' = target
        self._sz_types: Dict = {}  # dict with target sizes (cache used by sizeof)
        self._heap_next_free_addr: int = target_mem_start_addr
        self._target_mem_base_addr: int = target_mem_start_addr
        self._target_mem_num_bytes: int = target_mem_num_bytes
        self._zero_mem = zero_mem
        self.reset()

    def _bytes_needed(self, n):
        if n == 0:
            return 1
        return int(math.log(n, 256)) + 1

    def _write_raw(self, dst_addr: Union[int, str, TypedPtr], values: bytes) -> None:
        content = binascii.hexlify(struct.pack('<%dB' % len(values), *values)).decode('utf8')
        self._target.exec(f'-data-write-memory-bytes {dst_addr} "{content}"')

    def sizeof(self, target_type: str) -> int:
        """
        This function returns the size in bytes of the given target data type.

        Args:
            target_type: Name of the target data type.

        Returns:
            The size in bytes of the data type on target.
        """
        if target_type not in self._sz_types.keys():
            try:
                sz = int(self._target.eval('sizeof(%s)' % target_type))
                self._sz_types[target_type] = sz
            except:
                log.error('Unable to determine size for target type %s' % target_type)

        return self._sz_types[target_type]

    def write(self, dst_addr: Union[int, str, TypedPtr], val: Union[int, bytes, str], cnt: int = 1) -> None:
        """
        This function writes the provided data to target memory at destination address. If cnt is other than one,
        the provided data is replicated cnt times.

        Args:
            dst_addr: The target's destination memory address to write to.
            val: Content to be written to the target.
            cnt: The number of times val shall be repeated when writing to the target.
        """
        if isinstance(val, int):
            # note: int.to_bytes raises exception if type_sz != val size
            bval = val.to_bytes(self._bytes_needed(val), byteorder=self._target.byte_order)
            self._write_raw(dst_addr, bval * cnt)
        elif isinstance(val, bytes):
            self._write_raw(dst_addr, val * cnt)
        elif isinstance(val, str):
            bval = bytes(val, encoding='ascii')
            self._write_raw(dst_addr, bval * cnt)
        else:
            raise ValueError('Only int, bytes or str (ascii) are supported as val types')

    def read(self, src_addr: Union[int, str, TypedPtr], num_bytes: int) -> bytes:
        """
        This function reads the requested number of bytes from the specified source address.

        Args:
            src_addr: The target's source memory address to read from.
            num_bytes: The number of bytes to read from target memory.

        Returns:
            Returns the bytes read from the target.
        """
        num_remaining: int = num_bytes
        if isinstance(src_addr, int):
            addr_to_read = src_addr
        elif isinstance(src_addr, str):
            addr_to_read = int(src_addr, 10)
        elif isinstance(src_addr, TypedPtr):
            addr_to_read = src_addr.addr
        else:
            raise ValueError('Illegal type for src_addr')
        content = ''

        while num_remaining > 0:
            bytes_to_read = 1024
            if num_remaining < 1024:
                bytes_to_read = num_remaining

            data = self._target.exec(f'-data-read-memory-bytes -o 0 {addr_to_read} {bytes_to_read}')
            buf = data['payload']['memory'][0]['contents']
            buf_len = len(buf) / 2
            content += buf

            num_remaining -= buf_len
            addr_to_read += buf_len

        return binascii.unhexlify(content)

    def reset(self) -> None:
        """
        This function resets the on-target memory. It sets the next_element pointer back to the first element and it
        zeros out the on-target memory region used for memory allocation.
        """
        self._heap_next_free_addr = self._target_mem_base_addr
        if self._zero_mem:
            # note: bytes(sz) creates zero-filled bytes object of length sz
            self.write(self._target_mem_base_addr, bytes(self._target_mem_num_bytes))

    def alloc(self, req_num_bytes: int, var_name: str = None, align: int = ALIGN_DEFAULT) -> TypedPtr:
        """
        This function allocates the requested number of bytes on the target device. The allocated memory is guaranteed
        to be word (32bit aligned). Optionally, a GDB convenience variable with the provided variable name is created
        which can be optionally used to reference the allocated memory in GDB commands.

        Args:
            req_num_bytes: Requested number of bytes.
            var_name: Optional GDB variable name used for the newly allocated memory.
            align: Alignment for allocated memory. Default is 4 bytes.

        Returns:
            Returns the address of the allocated on-target memory as a TypedPtr.
        """
        align_delta: int = 0
        if self._heap_next_free_addr % align != 0:
            align_delta = align - (self._heap_next_free_addr % align)

        # number of bytes still available on target for memory allocation
        avail_bytes: int = (self._target_mem_base_addr + self._target_mem_num_bytes) - (self._heap_next_free_addr + align_delta)

        assert(req_num_bytes <= avail_bytes), 'unable to allocate %d bytes of on-target memory' % req_num_bytes

        addr: int = self._heap_next_free_addr + align_delta
        self._heap_next_free_addr += align_delta + req_num_bytes

        if var_name is not None:
            self._target.cli_exec(f'set var {var_name} = (void*){addr}')

        return TypedPtr(self._target, addr, 'void')

    def alloc_type(self, var_type: str, val: Union[int, bytes, str] = None, cnt: int = 1, var_name: str = None, align: int = ALIGN_DEFAULT) -> TypedPtr:
        """
        This function allocates on-target memory for cnt number of variables of the specified type. The start of the
        allocated memory is guaranteed to be word (32bit aligned). If the memory is allocated for, e.g., for an array
        holding elements of a composite type with size not being a multiple of words, this function does not guarantee
        word alignment from the second array element onwards. In other word, this function simply allocates memory
        of size = sizeof(var_type) * cnt.
        Optionally, the allocate memory can be initialized with the provided value.
        Optionally, a GDB convenience variable with the provided variable name is created which can be used to reference
        the allocated memory in GDB commands.

        Args:
            var_type: Type of variable to be allocated on-target.
            val: Value for the newly assigned variable. Note that if cnt > 1 this value is set for all the elements.
            cnt: Number of elements to be allocated.
            var_name: Optional GDB variable name used for the newly allocated memory.
            align: Alignment for allocated memory. Default is 4 bytes.

        Returns:
            Returns the address of the allocated on-target memory as a TypedPtr.
        """
        type_sz: int = self.sizeof(var_type)
        p_var: TypedPtr = self.alloc(type_sz * cnt, var_name, align)
        if val is not None:
            self.write(p_var, val, cnt)

        # optionally create a gdb convenience variable and cast to concrete type as specified by var_type
        if var_name is not None:
            self._target.cli_exec('set var %s = (%s*)%s' % (var_name, var_type, var_name))
        return TypedPtr(self._target, p_var.addr, var_type)

    def get_num_alloc_bytes(self) -> int:
        """
        Returns: Number of bytes allocated since last call to TargetMem::reset.
        """
        return self._heap_next_free_addr - self._target_mem_base_addr


# -------------------------------------------------------------------------------------------------
class TargetMemTestHook(TargetMem):
    """
    This class implements a variation of the TargetMem class which is intended to be used if the DOTT_test_hook is
    used for on-target memory allocation. In addition to setting the correct memory address (in stack from of the
    test hook) this class also checks that allocation is only performed if the target is halted in the context of the
    test hook.
    """
    def __init__(self, target: 'Target'):
        start_addr = target.eval('dbg_mem_u32')
        num_bytes = int(target.eval('dbg_mem_u32_sz'))
        super().__init__(target, start_addr, num_bytes)

    def alloc(self, req_num_bytes: int, var_name: str = None, align: int = ALIGN_DEFAULT):
        try:
            self._target.eval('dbg_mem_u32')  # raises exception if symbol is not accessible in current context
        except:
            raise DottException('Test-hook based memory allocation is only possible '
                                'if program is halted in the test hook!') from None
        return super().alloc(req_num_bytes, var_name, align)

    def alloc_type(self, var_type: str, val: Union[int, bytes, str] = None, cnt: int = 1, var_name: str = None, align: int = ALIGN_DEFAULT):
        try:
            self._target.eval('dbg_mem_u32')  # raises exception if symbol is not accessible in current context
        except Exception:
           raise DottException('Test-hook based memory allocation is only possible '
                               'if program is halted in the test hook!') from None

        return super().alloc_type(var_type, val, cnt, var_name, align)


# -------------------------------------------------------------------------------------------------
class TargetMemNoAlloc(TargetMem):
    """
    This class implements a variation of the TargetMem class which actually does not allow on-target memory allocation.
    Target memory bulk read and write still are supported.
    """
    def __init__(self, target: 'Target'):
        start_addr = 0xffffffff
        num_bytes = 0
        super().__init__(target, start_addr, num_bytes)

    def alloc(self, req_num_bytes: int, var_name: str = None, align: int = ALIGN_DEFAULT) -> TypedPtr:
        raise Exception('On-target memory allocation not supported in by this memory model!')

    def alloc_type(self, var_type: str, val: Union[int, bytes, str] = None, cnt: int = 1, var_name: str = None, align: int = ALIGN_DEFAULT) -> TypedPtr:
        raise Exception('On-target memory allocation not supported in by this memory model!')

    def reset(self) -> None:
        return


# -------------------------------------------------------------------------------------------------
class TargetMemScoped(object):
    """
    This class implements a form of on-target, on-stack memory allocation with a limited scope. In contrast to the
    test hook approach, this allocation technique can be used at every location the program can be halted. At this
    halt location, it enables users to grab a chunk of memory which is located on the current stack as indicated by
    SP. If this is MSP or PSP is not checked.
    It returns a TargetMem instance which can be used to allocate memory blocks within this on-target memory chunk.
    These allocated memory regions can then be populated and used as arguments in on-target function calls using
    'eval(...)'. At the end of the 'with ... as' statement, the chunk of on target memory is 'returned' to the target
    by re-adjusting the stack pointer accordingly.

    Example:
        # - grab a chunk of 128 bytes of on-target (stack) memory
        # - within this chunk, allocate an array with 5 uint16_t variables
        # - fill the array, use it as function call parameter
        # - note: outside the scope of the 'with ... as', the m.alloc functions are unavailable as the chunk of
        #   on-target stack is already returned to the target system.

        with TargetMemScoped(dott().target, 128) as m:
            elements = [0, 1, 2, 65535, 99]
            addr = m.alloc_type('uint16_t', cnt=len(elements), val=0x0)
            for i in range(len(elements)):
                dott().target.eval(f'{addr}[{i}] = {elements[i]}')
            res = dott().target.eval(f'example_SumElements({addr}, {len(elements)})')
            assert (sum(elements) == res), f'expected: {sum(elements)}, is: {res}'
    """
    def __init__(self, target: 'Target', num_bytes: int, suppress_warnings: bool = False):
        """
        Constructor.

        Args:
            target: The target instance on which the memory shall be allocated.
            num_bytes: The number of bytes the chunk of memory shall be able to hold. Note: This value is internally
                     increased to the next value where num_bytes % 8 == 0 to ensure double-world alignment of the stack.
            suppress_warnings: Suppress warnings which would be issued if the SP and PC are not having the expected
                     values when leaving the 'with ... as' block.
        """
        self._target: 'Target' = target
        self._pc_init: int = 0x0  # the program counter upon entering the 'with' block
        self._sp_init: int = 0x0  # the stack pointer upon entering the 'with' block
        self._sp_init_dec: int = 0x0  # the decremented _sp_init
        self._mem: TargetMem = None
        # ensure that the requested number of bytes is a multiple of 8 (double-word alignment of stack; cp.
        # "Procedure Call Standard for the Arm® Architecture").
        if num_bytes % 8 != 0:
            num_bytes += 8 - (num_bytes % 8)
        self._num_bytes: int = num_bytes  # the size in bytes of the on-target memory chunk
        self._suppress_warnings: bool = suppress_warnings

    def __enter__(self) -> TargetMem:
        if self._target.is_running():
            raise DottException('Target must be halted when initializing scoped on-target memory.')

        # save current stack pointer and program counter
        self._sp_init = self._target.eval('$sp')
        self._pc_init = self._target.eval('$pc')

        # (1) set decremented SP equal to current SP
        self._sp_init_dec = self._sp_init

        # (2) check if SP is double-word aligned. if not, do so.
        if self._sp_init_dec % 8 != 0:
            # Arm 'Procedure Call Standard for the Arm Architecture' requires double-word alignment on
            # 'public interface' (i.e., when calling functions).
            log.warn('Current SP is not double-word aligned! Correcting alignment for allocated memory.')
            self._sp_init_dec += 8 - (self._sp_init_dec % 8)

        # (3) decrement SP
        # Note: Stack is "full-descending" (see 'Procedure Call Standard for the Arm Architecture').
        #       That means the SP points to the last used (full)  entry and the stack grows down (descends).
        self._sp_init_dec -= self._num_bytes  # decrement (descend) SP

        # Finally, adjust the SP to reserve the requested chunk of the stack. Create and return a memory manager for it.
        self._target.eval(f'$sp = {self._sp_init_dec}')
        self._mem = TargetMem(self._target, self._sp_init_dec, self._num_bytes)
        return self._mem

    def __reset_sp(self):
        pc_curr = self._target.eval('$pc')
        sp_curr = self._target.eval('$sp')

        sp_pc_ok: bool = True

        # check if SP and PC are as expected
        if sp_curr != self._sp_init_dec:
            sp_pc_ok = False
            if not self._suppress_warnings:
                log.warn(f'Stack pointer is not as expected (expected: 0x{self._sp_init_dec:x}, act: 0x{sp_curr:x}). '
                         f'You should not alter execution flow within "with" block os scoped memory by using DOTT '
                         f'functions such as "cont", "ret", "step", and "step_inst" etc.!')
        if pc_curr != self._pc_init:
            sp_pc_ok = False
            if not self._suppress_warnings:
                log.warn(f'Program counter is not as expected (expected: 0x{self._pc_init:x}, actual: 0x{pc_curr:x}). '
                         f'You should not alter execution flow within "with" block os scoped memory by using DOTT '
                         f'functions such as "cont", "ret", "step", and "step_inst" etc.!')

        if sp_pc_ok:
            self._target.eval(f'$sp = {self._sp_init}')
        else:
            if not self._suppress_warnings:
                log.warn('Not undoing stack memory allocation at end of "with" statement!')

    @staticmethod
    def __func_unavailable(*args) -> None:
        log.warn("The functions 'alloc', 'alloc_type', and 'reset' are no longer available after the 'with ... as' "
                 "block of TargetMemScoped!")

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Note: We are not checking if there was an exception. We are always undoing (rolling back)
        # the on-stack memory allocation.

        if self._target.is_running():
            raise DottException('Target must be halted when leaving "with" block of scoped on-target memory.')

        # reset the internal state of the TargetMem instance with respect to the memory it managed.
        self._mem.reset()
        # reset the SP to the state it had before the 'with' block
        self.__reset_sp()
        # make alloc/reset functions of the TargetMem instance unusable after the 'with' block.
        self._mem.alloc = self.__func_unavailable
        self._mem.alloc_type = self.__func_unavailable
        self._mem.reset = self.__func_unavailable
