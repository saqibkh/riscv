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
#
#
# This file contains the helper function for the implementation of EDDI (EDDI)
# All instructions within a basic block are duplicated, and compare instructions are placed
# after each original store and branch instruction.
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


class EDDI:
    def __init__(self, i_map):
        self.simlog = i_map.simlog
        self.original_map = i_map
        self.used_registers_list = []
        self.used_floating_registers_list = []
        self.duplicate_register_list = []
        self.duplicate_floating_register_list = []
        self.function_names = []

        self.new_asm_file = self.original_map.file_asm
        self.function_names = utils.extract_function_names_asm(self.new_asm_file)
        self.generate_used_registers_list()
        self.generate__duplicate_register_list()
        self.generate_EDDI_file_update()
        self.initialize_duplicate_register()

    # This function will find and replace the operand with its duplicate
    # Note; it is important to match the operands otherwise mv a5, fa5 will be replaced with mv s3, fs3
    def replace_operands_with_duplicate(self, i_original_line, i_original_operand, i_duplicate_operand):
        i_inst = (i_original_line.split(' '))[0].split('\t')[0]
        i_new_line = i_inst + "\t"
        i_operands = ((i_original_line.split(' '))[-1].split('\t')[-1]).split(',')
        for i in range(len(i_operands)):
            if (i_original_operand in i_operands[i]) and not (("f" + i_original_operand) in i_operands[i]):
                i_operands[i] = i_operands[i].replace(i_original_operand, i_duplicate_operand)
            i_new_line += i_operands[i] + ","

        i_new_line = i_new_line[:-1]
        del i, i_duplicate_operand, i_inst, i_original_operand, i_operands
        return i_new_line

    # This function will be used to list of registers that duplicate the original registers.
    def generate__duplicate_register_list(self):
        # Step 0: Seperate general and floating point registers in self.used_register_list
        l_original_registers = []
        l_original_floating_registers = []
        for i in range(len(self.used_registers_list)):
            if self.used_registers_list[i].startswith('a') or self.used_registers_list[i].startswith('s') or \
                    self.used_registers_list[i] == 'gp':
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

            elif "\tcall" in i_line:
                l_func = (i_line.split('\tcall\t')[-1]).split('\tcall ')[-1]
                # Only initialize registers if a native function is called because we don't know if they will modify
                # the register and not restore it.
                # printf doesn't modify register
                if (l_func not in self.function_names) and (l_func != 'printf'):
                    for i in range(len(self.used_registers_list)):
                        self.new_asm_file.insert(i_line_num + 1,
                                                 '\tmv\t' + self.duplicate_register_list[i] + "," +
                                                 self.used_registers_list[i])
                    for i in range(len(self.used_floating_registers_list)):
                        self.new_asm_file.insert(i_line_num + 1,
                                                 '\tfmv.d.x\t' + self.duplicate_floating_register_list[i] + ",t0")
                        self.new_asm_file.insert(i_line_num + 1,
                                                 '\tfmv.x.d\tt0,' + self.used_floating_registers_list[i])

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
    def generate_EDDI_file_update(self):
        i_line_num = 0
        l_operands_to_check = []
        # 1. Loop the asm file lines until the end of file
        while i_line_num < len(self.new_asm_file):
            i_line = self.new_asm_file[i_line_num]
            if self.is_instruction_asm(i_line):
                i_line = i_line.split('\t', 1)[-1]
                # The instruction could be one of the three types of instructions,
                # 1) Arithmetic
                # 2) Load/Store
                # 3) Branch instruction
                if utils.is_arithmetic_instruction(i_line) or utils.is_floating_arithmetic_instruction(i_line):
                    l_operands = utils.get_unique_operands(i_line)
                    for i in range(len(l_operands)):
                        if (l_operands[i] in self.used_registers_list) or \
                                (l_operands[i] in self.used_floating_registers_list):
                            i_line = self.replace_operands_with_duplicate(i_line, l_operands[i],
                                                    self.get_corresponding_duplicate_register(l_operands[i]))

                    # We are not checking the value of ra (See notes above)
                    if l_operands[0] != 'ra':
                        i_line_num += 1
                        self.new_asm_file.insert(i_line_num, '\t' + i_line)

                elif utils.is_load_store_instruction(i_line) or utils.is_floating_load_store_instruction(i_line):
                    l_operands = utils.get_unique_operands(i_line)
                    for i in range(len(l_operands)):
                        if (l_operands[i] in self.used_registers_list) or \
                                (l_operands[i] in self.used_floating_registers_list):
                            i_line = self.replace_operands_with_duplicate(i_line, l_operands[i],
                                                                          self.get_corresponding_duplicate_register(
                                                                              l_operands[i]))

                    # We are not checking the value of ra (See notes above)
                    if l_operands[0] != 'ra':
                        if utils.is_store_instruction(i_line) and not utils.is_floating_store_instruction(i_line):
                            if l_operands[0] in self.used_floating_registers_list:
                                self.new_asm_file.insert(i_line_num, '\t' + "feq.d\tt0," + l_operands[0] + "," +
                                                         self.get_corresponding_duplicate_register(l_operands[0]))
                                self.new_asm_file.insert(i_line_num, '\t' + "bne\tt0,zero," + utils.exception_handler_address)
                                i_line_num += 2
                            else:
                                self.new_asm_file.insert(i_line_num, '\t' + "bne\t" + l_operands[0] + "," +
                                                         self.get_corresponding_duplicate_register(l_operands[0]) + "," +
                                                         utils.exception_handler_address)
                                i_line_num += 1

                        # Duplicate the instruction
                        i_line_num += 1
                        self.new_asm_file.insert(i_line_num, '\t' + i_line)

                elif utils.is_branch_instruction(i_line):
                    # For conditional branch, check that the operands and their duplicates match are in the
                    # l_operands_to_check list
                    if utils.is_conditional_branch_instruction(i_line):
                        for i in range(len(l_operands)):
                            if l_operands[i] in self.used_registers_list:
                                if l_operands[i] not in l_operands_to_check:
                                    l_operands_to_check.append(l_operands[i])

                    for i in range(len(l_operands_to_check)):
                        i_line_num += 1
                        self.new_asm_file.insert(i_line_num, '\t' + "bne\t" + l_operands_to_check[i] + "," +
                                                 self.get_corresponding_duplicate_register(
                                                     l_operands_to_check[i]) + "," +
                                                 utils.exception_handler_address)

                    # Clear the list once we have checked all necessary registers
                    l_operands_to_check = []

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
