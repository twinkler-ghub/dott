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

/*
 * Things to be tested:
 *
 * - intercepting functions and manipulating their return values
 * - implementing a test heap
 * - check how stack pointer advances
 */

#include "stdint.h"
#include "string.h"
#include "testhelpers.h"


typedef struct {
    uint8_t  paddA; // non-word size padding for testing purposes
    uint32_t a;
    uint8_t  paddB; // non-word size padding for testing purposes
    uint32_t b;
    uint8_t  paddC; // non-word size padding for testing purposes
    uint32_t sum;
} my_add_t;


/**
 * Function without any arguments.
 */
uint32_t __attribute__((used)) example_NoArgs(void)
{
	return 42;
}


/**
 * Static function without any arguments.
 */
static uint32_t __attribute__((used)) example_NoArgsStatic(void)
{
    volatile uint32_t val = 42;
	return val;
}


/**
 * Function with simple scalar arguments.
 */
uint32_t __attribute__((used)) example_Addition(uint32_t a, uint32_t b)
{
	return a + b;
}


/**
 * Function with pointer arguments,
 */
uint32_t __attribute__((used)) example_AdditionPtr(uint32_t *const a, uint32_t *const b)
{
	return *a + *b;
}



/**
 * Function with pointer arguments and pointer-based return value.
 */
uint32_t __attribute__((used)) example_AdditionPtrRet(uint32_t *const a, uint32_t *const b, uint32_t *sum)
{
	*sum = *a + *b;
	return *sum;
}


/**
 * Function with struct as argument.
 */
uint32_t __attribute__((used)) example_AdditionStruct(my_add_t ms)
{
	DOTT_VAR_KEEP(ms); // prevent compiler from optimizing out ms
	ms.sum = ms.a + ms.b;
	DOTT_LABEL("example_AdditionStruct_EXIT");
	return ms.sum;
}


/**
 * Function with pointer to struct as argument.
 */
uint32_t __attribute__((used)) example_AdditionStructPtr(my_add_t *ms)
{
	ms->sum = ms->a + ms->b;
	return ms->sum;
}



/**
 * Local function returning an integer.
 */
static uint32_t __attribute__((used)) DOTT_NO_OPTIMIZE example_GetA(void)
{
	uint32_t a = 42;
	return a;
}



/**
 * Local function returning an integer via pointer argument.
 */
static uint32_t  __attribute__((used)) DOTT_NO_OPTIMIZE example_GetB(uint32_t *const b)
{
	*b = 21;
	return 0;
}


/**
 * Function which calls two local functions to get the input for the computation.
 */
uint32_t __attribute__((used)) example_AdditionSubcalls(void)
{
	uint32_t a = example_GetA();
	uint32_t b;
	example_GetB(&b);

	return a + b;
}


/**
 * Function with many args (i.e., more args than can be passed via registers).
 */
uint32_t __attribute__((used)) example_ManyArgs(uint32_t a, uint32_t b, uint32_t c, uint32_t d, uint32_t e, uint32_t f)
{
	return a + b + c + d + e + f;
}


/**
 * Function taking two arguments, adding the second to the first and returning
 * the result.
 */
int32_t __attribute__((used)) example_FunctorAdd(int32_t a, int32_t b)
{
	return a + b;
}


/**
 * Function taking two arguments, subtracting the second from the first and
 * returning the result.
 */
int32_t __attribute__((used)) example_FunctorSub(int32_t a, int32_t b)
{
	return a - b;
}


/**
 * Function taking a function pointer and two integer arguments. It 'executes'
 * the function pointed to by the pointer on the two arguments and returns the
 * result.^
 */
int32_t __attribute__((used)) example_CustomOperation(int32_t (*func_ptr)(int32_t, int32_t), int32_t a, int32_t b)
{
	return (*func_ptr)(a, b);
}


/**
 * Function taking a string argument and returning the string's length.
 */
int32_t __attribute__((used)) example_StringLen(char *msg)
{
	return strlen(msg);
}


/**
 * Function which returns the sum of the elements in the provided array.
 */
static int32_t __attribute__((used)) example_SumElements(uint16_t *elem, uint16_t elem_sz)
{
	int32_t ret_val = 0;
	for (uint16_t i = 0; i < elem_sz; i++) {
		ret_val += elem[i];
	}
	return ret_val;
}




