#   Copyright (c) 2019 by Plexim GmbH
#   All rights reserved.
#
#   A free license is granted to anyone to use this software for any legal
#   non safety-critical purpose, including commercial applications, provided
#   that:
#   1) IT IS NOT USED TO DIRECTLY OR INDIRECTLY COMPETE WITH PLEXIM, and
#   2) THIS COPYRIGHT NOTICE IS PRESERVED in its entirety.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#   OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

include Controller_sources.mk

TSP_VERSION=2.3.3
TARGET_ROOT=C:/Users/temuu/Desktop/tsp_ti_c2000/ccs/28p55x
TOOLS_PATH=C:/Users/temuu/AppData/Local/Programs/PLECS C2000 TSP/cgt/ti-cgt-c2000_22.6.1.LTS
BIN_DIR=./output_TI28P55x
OUT_NAME=Controller
MAKEFILE=Controller.mk
LINKFILE=Controller.lkf
INSTALL_DIR=./
BASE_NAME=Controller
CCXML_FILE=
FLASH_EXE_PATH=C:/ti/uniflash_9.2.0/deskdb/content/TICloudAgent/win/ccs_base/DebugServer/bin/DSLite.exe

##############################################################
space:=
space+=
# for MacOS - NOTE: not tolerant to leading spaces or already escaped spaces '\ '
EscapeSpaces=$(subst $(space),\$(space),$(1))
FlipSlashesBack=$(subst /,\,$(1))

ifeq ($(OS),Windows_NT)
# Windows
SHELL := cmd.exe
FixPath=$(call FlipSlashesBack,$(1))
ClearFile=del /F /Q "$(call FlipSlashesBack,$(1))"
ClearDir=del /F /Q "$(call FlipSlashesBack,$(1))\*.*"
MoveFile=move /Y "$(call FlipSlashesBack,$(1))" "$(call FlipSlashesBack,$(2))"
CopyFile=copy /Y "$(call FlipSlashesBack,$(1))" "$(call FlipSlashesBack,$(2))"
TouchFile=type nul > "$(call FlipSlashesBack,$(1))"

else
# Linux style
FixPath = $(1)
ClearFile=rm -Rf "$(1)"
ClearDir=rm -Rf "$(1)"/*
MoveFile=mv "$(1)" "$(2)"
CopyFile=cp "$(1)" "$(2)"
TouchFile=touch "$(1)"

endif 

##############################################################

C_SOURCE_FILES=\
$(BASE_NAME)_hal.c \
$(BASE_NAME)_main.c\
dispatcher.c \
power.c \
f28p55x_devinit.c\
f28p55x_globalvariabledefs.c\
f28p55x_adc.c \
dio_28p55x.c \
sci_28p55x.c \
epwm_type4.c \
ain_type5.c \
dac_type2.c \
qep.c \
ecap_type3.c \
mcan_type0.c \
spi_type2.c \
csv.c \
stack_monitor.c \
uart.c \

#CLA_SOURCE_FILES=\
#$(BASE_NAME)_cla.cla

GENERATED_HEADERS=

CLA_SOURCE_FILES=\
$(BASE_NAME)_cla.cla

ASM_SOURCE_FILES=\
f28p55x_codestartbranch.asm\
f28p55x_usdelay.asm\
dispatcher_asm.asm

CGT_EXE_PATH=$(TOOLS_PATH)/bin
CGT_LIB_PATH=$(TOOLS_PATH)/lib
CGT_INC_PATH=$(TOOLS_PATH)/include

BIN_DIR_OS=$(call FixPath,$(BIN_DIR))

# compiler / assembler
C_OPTIONS=\
-D_PLEXIM_\
-DCPU1\
-DBASE_NAME=$(BASE_NAME)\
-DEXTERNAL_MODE=1\
-fr$(BIN_DIR)\
-fs$(BIN_DIR)\
-v28 \
-ml \
-mt \
--float_support=fpu32 \
--fp_mode=relaxed \
--float_operations_allowed=all \
-O0 \
--include_path="$(TARGET_ROOT)/app" \
--include_path="$(TARGET_ROOT)/../pil" \
--include_path="$(TARGET_ROOT)/../shrd" \
--include_path="$(TARGET_ROOT)/../inc" \
--include_path="$(TARGET_ROOT)/inc_impl" \
--include_path="$(TARGET_ROOT)/tiinc" \
--include_path="$(TARGET_ROOT)/tiinc/driverlib" \
--include_path="$(TARGET_ROOT)/../dcl/include" \
--include_path="$(TOOLS_PATH)/include" \
--include_path="./" \
-g \
--symdebug:dwarf_version=3\
--abi=eabi \
--cla_support=cla2 \
--tmu_support=tmu1 \
--c11 \
--printf_support=full \
\

L_OPTIONS=$(LINKFILE)

C_OBJFILES=$(patsubst %.c, $(BIN_DIR)/%.obj, $(C_SOURCE_FILES)) \
  $(patsubst %.c, $(BIN_DIR)/%.obj, $(SOURCE_FILES)) \
  $(patsubst %.cla, $(BIN_DIR)/%.obj, $(CLA_SOURCE_FILES))

ASM_OBJFILES=$(patsubst %.asm, $(BIN_DIR)/%.obj, $(ASM_SOURCE_FILES))

OBJFILES=$(C_OBJFILES) $(ASM_OBJFILES)

DEPENDFILES=$(patsubst %.c, $(BIN_DIR)/%.d, $(C_SOURCE_FILES)) $(patsubst %.cla, $(BIN_DIR)/%.d, $(CLA_SOURCE_FILES))

L_DEPENDENCIES=\
	$(LINKFILE) \
	$(call EscapeSpaces,$(TARGET_ROOT))/../pil/pil_c28_fpu32_eabi.lib \
	$(call EscapeSpaces,$(TARGET_ROOT))/tisrc/driverlib/plx_driverlib_fpu32_eabi.lib \
	$(call EscapeSpaces,$(TARGET_ROOT))/tisrc/driverlib/SFO_v8_fpu_lib_build_c28_driverlib.lib

# make all variables available to sub-makes
export

# Top level 
##########################################################################
all: $(MAKEFILE).uptodate
ifneq ($(wildcard $(BIN_DIR_OS)),  $(BIN_DIR_OS))
	"$(MAKE)" -f $(MAKEFILE) clean
endif
	"$(MAKE)" -f $(MAKEFILE) $(BIN_DIR)/$(OUT_NAME).elf
	
# Download
##########################################################################rm C
$(BIN_DIR)/$(BASE_NAME).ccxml:	$(call EscapeSpaces,$(CCXML_FILE)) $(MAKEFILE)
							$(call CopyFile,$(CCXML_FILE),$(BIN_DIR)/$(BASE_NAME).ccxml)

ifneq ($(and $(FLASH_EXE_PATH),$(CCXML_FILE)),)
download: $(BIN_DIR)/$(OUT_NAME).out $(BIN_DIR)/$(BASE_NAME).ccxml
	"$(FLASH_EXE_PATH)" flash --flash --config=$(call FixPath,$(BIN_DIR)/$(BASE_NAME).ccxml) $(call FixPath,$(BIN_DIR)/$(OUT_NAME).out) -u
else
download:
	@echo "Download not configured."
endif
 
# Linker
##########################################################################
$(BIN_DIR)/$(OUT_NAME).elf:  $(BIN_DIR)/$(OUT_NAME).out
						$(call CopyFile,$(BIN_DIR)/$(OUT_NAME).out,$(INSTALL_DIR)/$(OUT_NAME).elf)

$(BIN_DIR)/$(OUT_NAME).out:  $(OBJFILES) $(L_DEPENDENCIES)
						"$(CGT_EXE_PATH)/cl2000" -z -i"$(CGT_LIB_PATH)" $(OBJFILES) $(L_OPTIONS)

# Generated dependencies
##########################################################################
#-include ($(DEPENDFILES)) -- disabled due to CGT bug: https://sir.ext.ti.com/jira/browse/EXT_EP-9771

# Force clean when makefile changes
##########################################################################
$(MAKEFILE).uptodate: $(MAKEFILE)
	"$(MAKE)" -f $(MAKEFILE) clean
	$(call TouchFile,$(MAKEFILE).uptodate)

# Explicit rules (we must use explicit rules to allow spaces in $(TARGET_ROOT))
##########################################################################
$(BIN_DIR)/dispatcher.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/dispatcher.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/dispatcher_asm.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/dispatcher_asm.asm
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/power.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/power.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/f28p55x_adc.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/tisrc/f28p55x_adc.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/f28p55x_globalvariabledefs.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/tisrc/f28p55x_globalvariabledefs.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/f28p55x_devinit.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/tisrc/f28p55x_devinit.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/f28p55x_codestartbranch.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/tisrc/f28p55x_codestartbranch.asm
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/f28p55x_usdelay.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/tisrc/f28p55x_usdelay.asm
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/epwm_type4.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/epwm_type4.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/ain_type5.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/ain_type5.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/dio_28p55x.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/src/dio_28p55x.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/qep.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/qep.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/sci_28p55x.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/src/sci_28p55x.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/spi_type2.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/spi_type2.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/dac_type2.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/dac_type2.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"
						
$(BIN_DIR)/ecap_type3.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/ecap_type3.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/mcan_type0.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/mcan_type0.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/csv.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/csv.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/stack_monitor.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/stack_monitor.c
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) "$<"

$(BIN_DIR)/uart.obj:	$(call EscapeSpaces,$(TARGET_ROOT))/../shrd/uart.c
						"$(CGT_EXE_PATH)"/cl2000 $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)"/cl2000 $(C_OPTIONS) "$<"

# Implicit Rules for generated files
##########################################################################
$(BIN_DIR)/%.obj:		%.c	$(GENERATED_HEADERS) $(MAKEFILE)
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) $<

$(BIN_DIR)/%.obj:		%.cla	$(MAKEFILE)
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) --preproc_dependency=$(patsubst %.obj,%.d,$@) "$<"
						"$(CGT_EXE_PATH)/cl2000" $(C_OPTIONS) $<

##########################################################################

clean:
ifeq ($(wildcard $(BIN_DIR_OS)),  $(BIN_DIR_OS))
	$(call ClearDir,$(BIN_DIR_OS))
else
	mkdir $(BIN_DIR_OS)
endif
