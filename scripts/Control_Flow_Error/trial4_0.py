import datetime
import random
import subprocess
import utils
import compileUtil
import fileinput
import execute_spike
import os
from os import path

###################################################################################################################
#
# This is a new type of error detection technique where the stack frame is checked after each function/procedure.
# The stack frame contains temp storage, local variables, saved registers etc.
# The top of the stack frame is the stack pointer ($sp) and the bottom of the stack is identified by
# frame pointer $fp. Just below the frame pointer is where we store all the arguments and return values.
#
#
###################################################################################################################


class TRIAL4_0:
    def __init__(self, i_map):
        self.simlog = i_map.simlog
        self.original_map = i_map

        # Registers that are to be checked at the input and output of each functions
        self.inputs_to_check = []
        self.outputs_to_check = []

        # Compile time signature
        self.compile_time_sig = []

        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm

        self.gather_registers_to_be_checked()

        self.inputs_to_check = self.sort_registers_to_check(self.inputs_to_check)
        self.outputs_to_check = self.sort_registers_to_check(self.outputs_to_check)

        # Generate instruction mapping between .s and .objdump file instructions
        if i_recalculate_reg_values:
            return

        # Generate the new assembly file
        utils.generate_instruction_mapping(self)
        self.generate_TRIAL3_2_file_updated()