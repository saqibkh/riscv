#!/usr/bin/python

import sys
import logging
import time
import string
import datetime
import random
import subprocess
import utils
from os import path


##############################################################################################################
#
# This file contains the helper function for the implementation of EDDDDI (ED4I)
# All instructions within a basic block are duplicated, and compare instructions are placed
# after each original and duplicate instruction.
#
# Original program must use a limit set of registers, so that we can use the rest of the
# registers as duplicate registers.
#
# Original Register      |     Duplicate register
#      s0/fp
#      s1
#      s2
#      s
#
#
#
#
#
#
#
#
#
#
##############################################################################################################


class EDDDDI:
    def __init__(self, i_map):
        self.simlog = i_map.simlog
        self.original_map = i_map
        self.used_registers_list = []

        self.new_asm_file = self.original_map.file_asm
        self.generate_used_registers_list()
        self.generate_EDDDDI_file_update()
        x = 1

    # This file create a modified assembly file that has duplicate instructions and their checks
    def generate_EDDDDI_file_update(self):

        i_line_num = 0

        # 1. Loop the asm file lines until the end of file
        while i_line_num < len(self.new_asm_file):

            i_line = self.new_asm_file[i_line_num]
            if self.is_instruction_asm(i_line):
                i_line = i_line.split('\t', 1)[-1]
                # The instruction could be one of the three types of instructions,
                # 1) Arithmetic
                # 2) Load/Store
                # 3) Branch instruction
                if utils.is_arithmetic_instruction(i_line) or utils.is_load_store_instruction(i_line):
                    self.new_asm_file.insert(i_line_num, '\t'+i_line)
                elif utils.is_branch_instruction(i_line):
                    x = 2
                else:
                    self.simlog.error("Unrecognized instruction: " + i_line)
                    raise Exception
            else:
                i_line_num += 1

    # This function populates the self.used_registers_list to show which registers are being used in the
    # actual program execution
    def generate_used_registers_list(self):
        for i in range(len(self.original_map.blocks)):
            for j in range(len(self.original_map.blocks[i].entries)):

                l_instruction = self.original_map.blocks[i].entries[j]
                l_operands = l_instruction.split('\t')[-1]
                l_operands = l_operands.split(',')

                # Example addi\tsp,sp,-48
                for k in range(len(l_operands)):

                    # Skip if it is a integer
                    if l_operands[k].isdigit() or l_operands[k].isnumeric() or l_operands[k].startswith('-'):
                        continue
                    # It is possible that the register is wrapped in brackets ()
                    # Example 40(sp)
                    elif '(' in l_operands[k]:
                        l_register = (l_operands[k].split('(')[-1]).split(')')[0]
                        if l_register not in self.used_registers_list:
                            self.used_registers_list.append(l_register)
                            continue
                    # Example: 0x40 and <counterSetBits + 0x30>
                    elif '0x' in l_operands[k]:
                        continue
                    # Example <counterSetBits + 0x30>
                    elif '<' in l_operands[k] and '>' in l_operands[k]:
                        continue

                    # There are few other things we need to ignore, like 'zero' or 'ret'
                    elif 'ret' in l_operands[k] or 'zero' in l_operands[k]:
                        continue

                    # Check if the register is already in the list. If not, then add it
                    else:
                        if l_operands[k] not in self.used_registers_list:
                            self.used_registers_list.append(l_operands[k])

    # Definition: checks if the provided line is a valid instruction in the asm file
    def is_instruction_asm(self, i_line):
        if not i_line.startswith('\t'):
            return False
        i_line = i_line.strip('\t')
        if i_line.startswith('.'):
            return False
        return True