/*
 *   Copyright (c) 2019-2021 ams AG
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */

/*
 Authors:
 - Thomas Winkler, ams AG, thomas.winkler@ams.com
*/


#include "stdint.h"
#include "string.h"

#include "testhelpers.h"

/**
 * This is the chained test hook which is used as entry point for the tests
 * executed on the host.
 *
 * \param dbg_mem_u32     Pointer to memory region used as scratchpad memory for the tests.
 * \param dbg_mem_u32_sz  Size of scratchpad memory in bytes.
 */
void DOTT_NO_OPTIMIZE DOTT_test_hook_chained(uint32_t *dbg_mem_u32, uint32_t dbg_mem_u32_sz)
{

}


/**
 * This method is used as entry point for debugger-based on target testing.
 * Note: For this function optimization is intentionally disabled to ensure that all variables and especially the label
 * are included in the final binary.
 */
void DOTT_NO_OPTIMIZE DOTT_test_hook(void)
{
    /* word-aligned junk of memory */
    uint32_t __attribute__ ((aligned (4))) dbg_mem_u32[64] = { 0, };
    goto test_start; /* silence gcc's 'unused label' warning; the label is not used in the code but for the tests */

test_start:

    DOTT_test_hook_chained(dbg_mem_u32, sizeof(dbg_mem_u32));
}


/**
 * Inline function which, when called, inserts a breakpoint into the code.
 * This function is intended for debugging purposes only.
 */
inline void DOTT_break_here(void)
{
    __asm volatile(
            "bkpt #0x01\n\t"
            "mov pc, lr\n\t"
    );
}
