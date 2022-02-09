#!/usr/bin/python

import sys
import logging
import time
import string
import datetime
import random
import subprocess
import utils
import registers
import instructions
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
# Note: We will duplicate instructions containing ra, but we won't check it's value because
#       it can change with jal (jump and link) instruction. It's not easy to calculate it's
#       value beforehand to be able to store in its duplicate register.
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
        self.used_floating_registers_list = []
        self.duplicate_register_list = []
        self.duplicate_floating_register_list = []

        self.new_asm_file = self.original_map.file_asm
        self.generate_used_registers_list()
        self.generate__duplicate_register_list()
        self.generate_EDDDDI_file_update()
        self.initialize_duplicate_register()

    # This function will be used to list of registers that duplicate the original registers.
    def generate__duplicate_register_list(self):
        # Step 0: Seperate general and floating point registers in self.used_register_list
        l_original_registers = []
        l_original_floating_registers = []
        for i in range(len(self.used_registers_list)):
            if self.used_registers_list[i].startswith('a') or self.used_registers_list[i].startswith('s'):
                l_original_registers.append(self.used_registers_list[i])
            elif self.used_registers_list[i].startswith('fa') or self.used_registers_list[i].startswith('fs'):
                l_original_floating_registers.append(self.used_registers_list[i])
            elif (self.used_registers_list[i] == 'ra') or (self.used_registers_list[i] == 'rtz'):
                continue
            else:
                self.simlog.error("Unrecognized register: " + self.used_registers_list[i])
                raise Exception
        self.used_registers_list = l_original_registers
        self.used_floating_registers_list = l_original_floating_registers
        del l_original_registers, l_original_floating_registers

        l_duplicate_registers = []
        l_duplicate_floating_registers = []
        # Step 1: Get a list of actual hardware general purpose registers that will be used for duplication
        for i in range(len(registers.possible_duplicate_registers)):
            if registers.possible_duplicate_registers[i] not in self.used_registers_list:
                l_duplicate_registers.append(registers.possible_duplicate_registers[i])
            # We only need X number of registers, where X is the number of registers used in original program
            if len(l_duplicate_registers) == len(self.used_registers_list):
                self.duplicate_register_list = l_duplicate_registers
                break
        if len(l_duplicate_registers) != len(self.used_registers_list):
            self.simlog.error("We don't have enough registers available to duplicate original registers")
            raise Exception

        # Step 2: Get a list of actual hardware floating point registers that will be used for duplication
        for i in range(len(registers.possible_duplicate_floating_registers)):
            if registers.possible_duplicate_floating_registers[i] not in self.used_floating_registers_list:
                l_duplicate_floating_registers.append(registers.possible_duplicate_floating_registers[i])
            # We only need X number of registers, where X is the number of registers used in original program
            if len(l_duplicate_floating_registers) == len(self.used_floating_registers_list):
                self.duplicate_floating_register_list = l_duplicate_floating_registers
                break
        if (len(l_duplicate_floating_registers) != len(self.used_floating_registers_list)) and \
                (len(self.used_floating_registers_list) != 0):
            self.simlog.error("We don't have enough floating point registers available to duplicate original registers")
            raise Exception

    def initialize_duplicate_register(self):
        for i_line_num in range(len(self.new_asm_file)):
            i_line = self.new_asm_file[i_line_num]
            if i_line == 'main:':
                for i in range(len(self.used_registers_list)):
                    self.new_asm_file.insert(i_line_num + 1,
                                             '\tmv\t' + self.duplicate_register_list[i] + "," +
                                             self.used_registers_list[i])
                for i in range(len(self.used_floating_registers_list)):
                    self.new_asm_file.insert(i_line_num + 1,
                                             '\tfmv.d.x\t' + self.duplicate_floating_register_list[i] + ",t0")
                    self.new_asm_file.insert(i_line_num + 1,
                                             '\tfmv.x.d\tt0,' + self.used_floating_registers_list[i])
                return

    def get_corresponding_duplicate_register(self, l_operand):
        for i in range(len(self.used_registers_list)):
            if l_operand == self.used_registers_list[i]:
                return self.duplicate_register_list[i]
        for i in range(len(self.used_floating_registers_list)):
            if l_operand == self.used_floating_registers_list[i]:
                return self.duplicate_floating_register_list[i]
        self.simlog.error("Failed to find a corresponding duplicate register for " + l_operand)
        raise Exception

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
                if i_line_num == 188:
                    x = 1
                if utils.is_arithmetic_instruction(i_line) or utils.is_floating_arithmetic_instruction(i_line):
                    l_operands = utils.get_unique_operands(i_line)
                    for i in range(len(l_operands)):
                        if l_operands[i] in self.used_registers_list:
                            i_line = i_line.replace(l_operands[i],
                                                    self.get_corresponding_duplicate_register(l_operands[i]))
                    # We are not checking the value of ra (See notes above)
                    if l_operands[0] != 'ra':
                        i_line_num += 1
                        self.new_asm_file.insert(i_line_num, '\t' + i_line)
                        if l_operands[0] in self.used_floating_registers_list:
                            i_line_num += 1
                            self.new_asm_file.insert(i_line_num, '\t' + "feq.d\tt0," + l_operands[0] + "," +
                                                     self.get_corresponding_duplicate_register(l_operands[0]))
                            i_line_num += 1
                            self.new_asm_file.insert(i_line_num,
                                                     '\t' + "bne\tt0,zero," + utils.exception_handler_address)
                        else:
                            i_line_num += 1
                            self.new_asm_file.insert(i_line_num, '\t' + "bne\t" + l_operands[0] + "," +
                                                     self.get_corresponding_duplicate_register(l_operands[0]) + "," +
                                                     utils.exception_handler_address)

                elif utils.is_load_store_instruction(i_line) or utils.is_floating_load_store_instruction(i_line):
                    l_operands = utils.get_unique_operands(i_line)
                    for i in range(len(l_operands)):
                        if l_operands[i] in self.used_registers_list:
                            i_line = i_line.replace(l_operands[i],
                                                    self.get_corresponding_duplicate_register(l_operands[i]))
                    # We are not checking the value of ra (See notes above)
                    if l_operands[0] != 'ra':
                        i_line_num += 1
                        self.new_asm_file.insert(i_line_num, '\t' + i_line)
                        if l_operands[0] in self.used_floating_registers_list:
                            i_line_num += 1
                            self.new_asm_file.insert(i_line_num, '\t' + "feq.d\tt0," + l_operands[0] + "," +
                                                     self.get_corresponding_duplicate_register(l_operands[0]))
                            i_line_num += 1
                            self.new_asm_file.insert(i_line_num, '\t' + "bne\tt0,zero," + utils.exception_handler_address)
                        else:
                            i_line_num += 1
                            self.new_asm_file.insert(i_line_num, '\t' + "bne\t" + l_operands[0] + "," +
                                                     self.get_corresponding_duplicate_register(l_operands[0]) + "," +
                                                     utils.exception_handler_address)

                elif utils.is_branch_instruction(i_line):
                    # No need to duplicate unconditional branches as there is nothing to check
                    if utils.is_unconditional_branch_instruction(i_line):
                        pass
                    # For conditional branch, check that the operands and their duplicates match
                    elif utils.is_conditional_branch_instruction(i_line):
                        for i in range(len(l_operands)):
                            if l_operands[i] in self.used_registers_list:
                                i_line_num += 1
                                self.new_asm_file.insert(i_line_num, '\t' + "bne\t" + l_operands[i] + "," +
                                                         self.get_corresponding_duplicate_register(l_operands[i]) +
                                                         "," + utils.exception_handler_address)
                # Skip a nop instruction
                elif i_line == 'nop':
                    pass
                else:
                    self.simlog.error("Unrecognized instruction: " + i_line)
                    raise Exception

                i_line_num += 1
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
                    elif 'ret' in l_operands[k] or 'zero' in l_operands[k] or 'nop' in l_operands[k]:
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
