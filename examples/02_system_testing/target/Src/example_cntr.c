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

#include "stddef.h"
#include "stdint.h"
#include "stdbool.h"
#include "string.h"

#include "stm32f0xx_hal.h"

#include "main.h"
#include "i2c.h"

#include "testhelpers.h"

// variable in BSS section (zero initialized; checked from host-side test)
static volatile uint32_t _sample_cnt = 0;
// variable in data section (initialized by loader; checked from host-side test)
static volatile uint32_t _test_data = 0xdeadbeef;
// counter variable for systick callback
static volatile uint32_t _tick_cnt = 0;
// counter variable for timer 7 (TIM7) interrupt
static uint32_t _timer_cnt = 0;


/*
 * Callback function called from STM32 HAL whenever the Systick timer advances.
 */
void HAL_SYSTICK_Callback()
{
	/* variables are used by example tests; make sure they are not removed */
	DOTT_VAR_KEEP(_sample_cnt);
	DOTT_VAR_KEEP(_test_data);

	_tick_cnt++;
}


/*
 * Called from TIM7 interrupt.
 */
void timer_advance()
{
	_timer_cnt++;
}
