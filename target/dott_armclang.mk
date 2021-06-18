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

# This Makefile was developed and tested with GNU make 4.1.

$(info DOTT is using Arm Clang (Arm Compiler 6))

# Note: CCPATH is the directory where the compiler is located (if it is not in PATH).
#       If required it shall be specified in the including Makefile

# Arm Compiler binaries
CC = $(CCPATH)armclang
AS = $(CCPATH)armasm
LD = $(CCPATH)armlink
AR = $(CCPATH)armar
FROMELF = $(CCPATH)fromelf
OBJCOPY = arm-none-eabi-objcopy
OBJDUMP = arm-none-eabi-objdump

# Check if armclang can be executed; otherwise exit with an error message
CCCHECK := $(shell $(CC) --version 2>&1 > /dev/null; echo $$?)
ifneq ($(CCCHECK),0)
  $(warning Arm compiler $(CC) not found. Either ensure that it is in the PATH or adjust the CCPATH accordingly!)
endif

# Flags passed to the assembler
ASFLAGS  = --cpu Cortex-M0 --li -g
ASFLAGS += --pd "__MICROLIB SETA 1"
ASFLAGS += --pd "ARMCM0 SETA 1"

# Flags passed to the C compiler
CFLAGS  = -xc -std=c99 --target=arm-arm-none-eabi -mcpu=cortex-m0 -mlittle-endian
CFLAGS += -fno-rtti -flto -funsigned-char -fshort-enums -fshort-wchar
CFLAGS += -MD -gdwarf-4 -Oz -ffunction-sections
CFLAGS += -D__MICROLIB -DARMCM0 -DCONF_LOGGING="1"

# Enable compiler warnings
WARNINGS  = -Wall
CFLAGS   += $(WARNINGS)

# Flags passed to the linker
LDFLAGS  = --cpu Cortex-M0 --lto
LDFLAGS += --library_type=microlib --strict
LDFLAGS += --map --load_addr_map_info --xref --callgraph --symbols
LDFLAGS += --summary_stderr --info summarysizes --info summarystack
LDFLAGS += --info sizes --info stack --info totals --info unused --info veneers
LDFLAGS += --list $(MAPFILE)

# archiver flags
ARFLAGS = --create
