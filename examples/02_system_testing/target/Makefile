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

.PHONY: default all clean

# Directory where the Makefile is located
MAKEFILEDIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

# OS detection; host OS is stored in the HOSTOS variable as Windows_NT or Linux.
ifeq ($(OS),Windows_NT)
  HOSTOS := $(OS)
else
  HOSTOS := $(shell uname -s)
  ifneq ($(HOSTOS),Linux)
    $(error Host OS could not be detected or is not supported!)
  endif
endif
$(info detected host OS: $(HOSTOS))

# Output folder for binary files
OUTDIR_BASE = build

# Source folder
SRCDIR = .

# CCPATH is the directory where Arm Compiler 6 (LLVM/CLang) binaries are located.
# If CCPATH is not specified (either here or in the environment) then the compiler is assumed to be in the PATH.
# Note: If CCPATH is specified it must include a trailing slash!
# Windows example: CCPATH = c:/Keil_v5/ARM/ARMCLANG/bin/
# Linux example:   CCPATH = /tools/ARMCLANG/bin/
# CCPATH =

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

# DOTT test framework
DOTTDIR=$(MAKEFILEDIR)/../../..
# set up DOTT variables depending on if DOTT was found or not
ifeq ("$(wildcard $(DOTTDIR))", "")
  # note: 'wildcard' returns empty if the provided directory does not exist
  $(info DOTT directory not found. Proceeding without DOTT...)
  DOTTDIR =
  DOTTINCDIRS = -I$(SRCDIR)/Application/no_dott
  DOTTLIB =
  DOTTCFLAGS = "-DCONF_USE_DOTT=0"
else
  $(info using DOTT in folder $(DOTTDIR))
  DOTTINCDIRS = -I$(DOTTDIR)/target/
  DOTTLIB = $(DOTTDIR)/target/build/dott_library.a
  DOTTCFLAGS = "-DCONF_USE_DOTT=1"
endif

# Flags passed to the assembler
ASFLAGS  = --cpu Cortex-M0 --li -g
ASFLAGS += --pd "__MICROLIB SETA 1"
ASFLAGS += --pd "ARMCM0 SETA 1"

# Flags passed to the C compiler
CFLAGS  = -xc -std=c99 --target=arm-arm-none-eabi -mcpu=cortex-m0 -mlittle-endian
CFLAGS += -fno-rtti -flto -funsigned-char -fshort-enums -fshort-wchar
CFLAGS += -MD -gdwarf-4 -Oz -ffunction-sections
CFLAGS += -D__MICROLIB -DARMCM0

# Enable compiler warnings
WARNINGS  = -Wall
CFLAGS   += $(WARNINGS)

# Include directories
INCDIRS  = -I$(MAKEFILEDIR)/Drivers/CMSIS/Include
INCDIRS += -I$(MAKEFILEDIR)/Inc
INCDIRS += -I$(MAKEFILEDIR)/Drivers/STM32F0xx_HAL_Driver/Inc
INCDIRS += -I$(MAKEFILEDIR)/Drivers/CMSIS/Device/ST/STM32F0xx/Include
INCDIRS += -I$(MAKEFILEDIR)/Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM0
INCDIRS += -I$(MAKEFILEDIR)/Middlewares/Third_Party/FreeRTOS/Source/include
INCDIRS += -I$(MAKEFILEDIR)/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS
INCDIRS += -I$(MAKEFILEDIR)/Drivers/CMSIS/Include
INCDIRS += -I$(DOTTDIR)/target
CFLAGS  += $(INCDIRS)

# CFLAGS for STM32 HAL
CFLAGS += -DUSE_HAL_DRIVER
CFLAGS += -DSTM32F072xB
CFLAGS += -D__weak="__attribute__((weak))"
CFLAGS += -D__packed="__attribute__((packed))"

# Flags passed to the linker
LDFLAGS  = --cpu Cortex-M0 --lto
LDFLAGS += --library_type=microlib --strict
LDFLAGS += --map --load_addr_map_info --xref --callgraph --symbols
LDFLAGS += --summary_stderr --info summarysizes --info summarystack
LDFLAGS += --info sizes --info stack --info totals --info unused --info veneers
LDFLAGS += --list $(MAPFILE)

# archiver flags
ARFLAGS = --create

# C source files to be built (shared between all binaries)
SRC = Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_i2c.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_i2c_ex.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_iwdg.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_spi.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_spi_ex.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_tim.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_tim_ex.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_uart.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_uart_ex.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_rcc.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_rcc_ex.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_gpio.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_dma.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_cortex.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_pwr.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_pwr_ex.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_flash.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_flash_ex.c \
      Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal_tim.c \
      Src/main.c \
      Src/dma.c \
      Src/gpio.c \
      Src/i2c.c \
      Src/usart.c \
      Src/tim.c \
      Src/stm32f0xx_it.c \
      Src/stm32f0xx_hal_msp.c \
      Src/system_stm32f0xx.c \
      Src/example_cntr.c \
      Src/example_cmd.c

# Assembly source files to be built (shared between all binaries)
ASMSRC = Drivers/CMSIS/Device/ST/STM32F0xx/Source/Templates/arm/startup_stm32f072xb.s

# Create list of object files and add object directory prefix
OBJS  = $(ASMSRC:%.s=%.o)
OBJS += $(SRC:%.c=%.o)

# Create list of dependency files (generated via -MD) and include them
DEPS = $(OBJS:%.o=%.d)
-include $(DEPS)

# The default (first) target to build is 'all'
all: dott_example_02 dott_example_02_sram dott_example_02_noopt


# Build rule tempalte for a single object file from an assembly file
define AS_OUT_SUBDIR_RULE
$1/%.o: $(SRCDIR)/%.s
	$$(info [AS] $$< -> $$@)
	@mkdir -p $$(dir $$@)
	$(AS) $$(ASFLAGS) -o $$@ $$<
endef


# Build rule template for a single object file from a C source file
define CC_OUT_SUBDIR_RULE
$1/%.o: $(SRCDIR)/%.c
	$$(info [CC] $$< -> $$@)
	@mkdir -p $$(dir $$@)
	$(CC) -c $$(CFLAGS) -o $$@ $$<
endef


# Remove all build artifacts
clean:
	$(info [RM] $(OUTDIR_BASE))
	@rm -rf $(OUTDIR_BASE)


# Generic rule to link all objects into final ELF binary and create final firmware image
dott_%: $(DOTTLIB)
	$(eval MAPFILE = $(OUTDIR)/$@.map)
	$(eval BINFILE = $(OUTDIR)/$@.bin)
	$(eval ELFFILE = $(OUTDIR)/$@.axf)
	$(eval DISASFILE = $(OUTDIR)/$@.asm)
	$(info [LD] $(firstword $?))
	$(foreach OBJ,$(wordlist 2, $(words $?), $?), $(info $(DUMMY)     $(OBJ)))
	$(info $(DUMMY)     -> $(ELFFILE) (ELF Binary))
	$(LD) $(LDFLAGS) --list $(MAPFILE) $? -o $(ELFFILE)
	@$(FROMELF) --bin $(ELFFILE) --output $(BINFILE)
	@$(FROMELF) --disassemble $(ELFFILE) --text -a -c -d -e -s -t -z --interleave=source --output $(DISASFILE)
	@$(OBJCOPY) --input-target=binary --output-target=elf32-little --change-addresses=$(LMAADDR) \
	            --rename-section .data=.rodata,alloc,load,readonly,data,contents $(BINFILE) $(BINFILE).elf
	@$(OBJDUMP) -h $(BINFILE).elf

# Output directories (below OUTDIR_BASE)
OUTDIR_EX2 = $(OUTDIR_BASE)/dott_example_02
OUTDIR_EX2_SRAM = $(OUTDIR_BASE)/dott_example_02_sram
OUTDIR_EX2_NOOPT = $(OUTDIR_BASE)/dott_example_02_noopt
OUTDIRS = $(OUTDIR_EX2) $(OUTDIR_EX2_SRAM) $(OUTDIR_EX2_NOOPT)

# Instanitate object target templates based on outdir list 
$(foreach DIR, $(OUTDIRS), $(eval $(call CC_OUT_SUBDIR_RULE, $(DIR)))) 
$(foreach DIR, $(OUTDIRS), $(eval $(call AS_OUT_SUBDIR_RULE, $(DIR)))) 


# --- Firmware targets ---


dott_example_02: LMAADDR = 0x00000000
dott_example_02: LDFLAGS += --scatter stm32_armclang_flash.sct
dott_example_02: OUTDIR = $(OUTDIR_EX2)
dott_example_02: $(addprefix $(OUTDIR_EX2)/, \
                         $(OBJS) \
)

dott_example_02_sram: LMAADDR = 0x20000000
dott_example_02_sram: LDFLAGS += --scatter stm32_armclang_sram.sct
dott_example_02_sram: OUTDIR = $(OUTDIR_EX2_SRAM)
dott_example_02_sram: $(addprefix $(OUTDIR_EX2_SRAM)/, \
                         $(OBJS) \
)

dott_example_02_noopt: LMAADDR = 0x00000000
dott_example_02_noopt: LDFLAGS += --scatter stm32_armclang_flash.sct
dott_example_02_noopt: CFLAGS := $(filter-out -Oz, $(CFLAGS))
dott_example_02_noopt: CFLAGS += -O0
dott_example_02_noopt: OUTDIR = $(OUTDIR_EX2_NOOPT)
dott_example_02_noopt: $(addprefix $(OUTDIR_EX2_NOOPT)/, \
                         $(OBJS) \
                       )

