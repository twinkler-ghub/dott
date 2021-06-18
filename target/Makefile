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

# DOTT folder
DOTTDIR=$(MAKEFILEDIR)

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
OBJDIR = build

# Source folder
SRCDIR = .

# Scatter file (linker script) with memory layout
SCATTERFILE_FLASH = clare_scatter_flash.sct
SCATTERFILE_RAM   = clare_scatter_ram.sct

# CCPATH is the directory where Arm Compiler 6 (LLVM/CLang) binaries are located.
# If CCPATH is not specified (either here or in the environment) then the compiler is assumed to be in the PATH.
# Note: If CCPATH is specified it must include a trailing slash!
# Windows example: CCPATH = c:/Keil_v5/ARM/ARMCLANG/bin/
# Linux example:   CCPATH = /tools/ARMCLANG/bin/
# CCPATH =

ifeq ($(USE_GCC), 1)
  include $(DOTTDIR)/dott_gcc.mk
else
  include $(DOTTDIR)/dott_armclang.mk
endif

# C Source files to be complied (shared between all binaries)
SRC = $(OBJDIR)/testhelpers.o

# disable LTO for test helpers object
$(OBJDIR)/testhelpers.o: CFLAGS:=$(filter-out -flto,$(CFLAGS))

# Assembly source files to be built (shared between all binaries)
ASMSRC =

# Create list of object files and add object directory prefix
OBJS  = $(ASMSRC:%.s=$(OBJDIR)/%.o)
OBJS += $(SRC:%.c=$(OBJDIR)/%.o)

# Create list of dependency files (generated via -MD) and include them
DEPS = $(OBJS:%.o=%.d)
-include $(DEPS)


# The default (first) target to build is 'all'
all: dott_library


# Build rule for a single object file from an assembly file
$(OBJDIR)/%.o: $(SRCDIR)/%.s
	$(info [AS] $< -> $@)
	@mkdir -p $(dir $@)
	$(AS) $(ASFLAGS) -o $@ $<


# Build rule for a single object file from a C source file
$(OBJDIR)/%.o: $(SRCDIR)/%.c
	$(info [CC] $< -> $@)
	@mkdir -p $(dir $@)
	$(CC) -c $(CFLAGS) -o $@ $<

# Remove all build artifacts
clean:
	$(info [RM] $(OBJDIR))
	@rm -rf $(OBJDIR)

# Link all objects into a static library
dott_%:
	$(eval LIBFILE = $(OBJDIR)/$@.a)
	$(info [LD] $(firstword $?))
	$(foreach OBJ,$(wordlist 2, $(words $?), $?), $(info $(DUMMY)     $(OBJ)))
	$(info $(DUMMY)     -> $(LIBFILE) (Static Library))
	$(AR) $(ARFLAGS) $(LIBFILE) $?

# Target for DOTT framework library
dott_library: $(OBJS)
