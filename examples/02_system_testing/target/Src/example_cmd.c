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

// size of a command packet read via I2C
#define CMD_PKT_SZ 9

// command packet IDs
#define CMD_ID_ADD 0x10
#define CMD_ID_BLINK 0x11

// flag which indicates that new command data is available in _data
static bool _data_ready = false;
// buffer holding new command data
static uint8_t _data[128] = {0, };
// buffer used by the DMA controller to store incoming I2C data
static uint8_t _recv_buf[128] = {0, };


/*
 * Struct used to hold a command ID plus command handler (function pointer).
 */
typedef struct command {
	uint8_t id;
	void (*func)(uint8_t*);
} command_t;


/*
 * Command handler which lets the status LED on the reference board blink.
 */
void cmd_led_blink(uint8_t *payload)
{
	HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_SET);
	HAL_Delay(500);
	HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_RESET);
}


/*
 * Command handler which computes the sum of two operands received via I2C.
 * The sum is not used any further but only inspected for correctness via a
 * host-side test.
 */
void cmd_add(uint8_t *payload)
{
	static uint32_t a, b, sum;
	a = payload[0] | payload[1] << 8 | payload[2] << 16 | payload[3] << 24;
	b = payload[4] | payload[5] << 8 | payload[6] << 16 | payload[7] << 24;
	sum = a + b;

	DOTT_VAR_KEEP(a);
	DOTT_VAR_KEEP(b);
	DOTT_VAR_KEEP(sum);

	DOTT_LABEL("CMD_ADD_EXIT");
}


/*
 * List of command IDs and corresponding command handlers (function pointers).
 */
command_t commands[] = {
		{CMD_ID_ADD, &cmd_add},
		{CMD_ID_BLINK, &cmd_led_blink},
		{0, NULL} // termination element; note: 0 is not a valid command id
};


/*
 * Application main loop which reads command packages from the I2C bus, looks
 * up the correct command handler and then calls the handler function.
 */
void app_main()
{
	// initial, non-blocking call to I2C receive function
	HAL_I2C_Slave_Receive_DMA(&hi2c1, _recv_buf, CMD_PKT_SZ);

	while(true) {

		if (_data_ready) {
			uint8_t cmd_id = _data[0];
			uint16_t i = 0;
			void (*func)(uint8_t*) = NULL;

			while(true) {
				if (commands[i].id == 0) {
					break;
				}

				if (commands[i].id == cmd_id) {
					func = commands[i].func;
					break;
				}

				i++;
			}

			// non-blocking call to I2C receive function
			HAL_I2C_Slave_Receive_DMA(&hi2c1, _recv_buf, CMD_PKT_SZ);
			_data_ready = false;

			DOTT_LABEL("I2C_READ_DONE");

			if (func != NULL) {
				func(_data + 1);
			} else {
				DOTT_LABEL("UNKNOWN_CMD");
				__NOP();
			}
		}
	}
}


/*
 * Callback called from STM32 HAL when an I2C DMA transfer is complete.
 */
void __attribute__((noinline)) HAL_I2C_SlaveRxCpltCallback(I2C_HandleTypeDef *hi2c)
{
	memcpy(_data, _recv_buf, 128);
	_data_ready = true;
}




