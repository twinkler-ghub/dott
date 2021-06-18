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


#ifndef UTILS_TESTHELPERS_H_
#define UTILS_TESTHELPERS_H_

/* Macro for different compilers to prevent optimization on a per-function
 * basis.
 */
#if defined (__ARMCC_VERSION) && (__ARMCC_VERSION >= 6010050)
    #define DOTT_NO_OPTIMIZE __attribute__((optnone))
    #define DOTT_NO_INLINE __attribute__((noinline))
#elif defined (__ARMCC_VERSION) && (__ARMCC_VERSION < 6000000)
    #define DOTT_NO_OPTIMIZE
    #define DOTT_NO_INLINE __attribute__((noinline))
#elif defined ( __GNUC__ )
    #define DOTT_NO_OPTIMIZE __attribute__((optimize("O0")))
    #define DOTT_NO_INLINE __attribute__((noinline))
#else
    #error Unsupported compiler.
#endif

/* Macro to set a label which can then be used by DOTT-based tests. */
#define DOTT_LABEL(NAME) __asm__("DOTT_LABEL_" NAME ":")
#define DOTT_LABEL_SAFE(NAME) __asm("nop"); \
                              __asm__("DOTT_LABEL_" NAME ":"); \
                              __asm("nop")


/*
 * Use the provided variable (memory "m" constraint) in a dummy inline assembly instruction such
 * that it is not optimized out. Clearly this comes at an context-specific expense in code size.
 */
#define DOTT_VAR_KEEP(NAME) __asm__ __volatile__("" :: "m" (NAME));

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Test hook to be called from main. Serves as entry point for host during test
 * execution.
 */
void DOTT_test_hook(void);

/*
 * Add a software breakpoint.
 */
void DOTT_break_here(void);

#ifdef __cplusplus
}
#endif

#endif /* UTILS_TESTHELPERS_H_ */
