#!/usr/bin/python

import logging
import time
import string
import datetime
import random
import subprocess
import re
import instructions
import registers
import utils
import execute_spike
from os import path

''' Start of class definitions'''


# TODO: We are currently assuming that each function is called only once. Thus the initial and final values
#       of a register are all static. This may not be true if a function is called multiple times with different
#       input values.
class Function:
    def __init__(self, i_name):
        # Name of the function such as main or countSetBits
        self.name = i_name

        # This var holds the name of the function which calls this particular function.
        # Main will have no parent function, but all others must have a parent/calling function.
        self.parent_function = None

        # List of functions that are called from within this particular function.
        # For example main calling printf and countSetBits
        self.list_sub_functions = []

        # List of block names that falls within these functions. The block names starts with "." in the asm file, such
        # as .L2, .L3 etc.
        self.list_blocks_names = []

        # Memory Addresses for the start and end of the function
        self.starting_address = None
        self.ending_address = []
        self.instructions = None

        # Holds the initial and final values of all registers
        self.initial_register_values = [[]]
        self.final_register_values = [[]]

        # List of registers that are used within this function
        self.registers_used = []
        # List of registers that are modified during this function (i.e. is a subset of registers_used
        self.registers_modified = []
        # List of registers that are not modified during this function (i.e. remaining subset of registers_used
        self.registers_unmodified = []

        # This is a list of registers that have different values at the start and end of a function.
        self.registers_different_values = []


class FunctionMap:
    ##
    # Description: initializes the ControlFlowMap class and
    #              processes the CFG blocks
    #
    # Inputs: f_asm and f_obj objects
    def __init__(self, i_C_executable_File, i_asm, i_util_functions):
        self.functions = []

        self.get_functions(i_asm)
        self.get_parent_function()
        self.get_instructions(i_util_functions)
        self.process_registers(i_C_executable_File)

    # Returns the ID of the function whose name matches with "i_func_name". Otherwise return None.
    def get_function_id_matching_name(self, i_func_name):
        for i in range(len(self.functions)):
            if self.functions[i].name == i_func_name:
                return i
        return None

    def get_parent_function(self):
        for i in range(len(self.functions)):
            for j in range(len(self.functions[i].list_sub_functions)):
                i_sub_function = self.functions[i].list_sub_functions[j]
                i_func_id = self.get_function_id_matching_name(i_sub_function)
                if i_func_id is not None:
                    self.functions[i_func_id].parent_function = self.functions[i].name

    # This function does the following things
    # 1. Gets the starting and ending addresses of each function
    # 2. Gets the register values at the start and end of each function
    # 3. Get a list of registers that are modified
    # 4. Fill the list of registers that weren't modified in the function
    # 5. Get a list of registers that are different from start and end along with their different values
    def process_registers(self, i_C_executable_File):
        # Get a list of registers whose value is used within the function
        for i in range(len(self.functions)):
            self.functions[i].registers_value_used = utils.registers_value_used_FunctionMap(
                self.functions[i].instructions.instruction)

        # Get a value of all registers at the start and end of each function
        for i in range(len(self.functions)):
            self.functions[i].initial_register_values = execute_spike.get_registers_values_at_address(
                i_C_executable_File.rsplit('.c')[0], self.functions[i].starting_address)
            self.functions[i].final_register_values = execute_spike.get_registers_values_at_address(
                i_C_executable_File.rsplit('.c')[0], self.functions[i].ending_address)

        # Get a list of registers that are used
        for i in range(len(self.functions)):
            self.functions[i].registers_used = utils.registers_used_FunctionMap(
                self.functions[i].instructions.instruction)

        # Get a list of registers that are modified
        for i in range(len(self.functions)):
            self.functions[i].registers_modified = utils.registers_modified_FunctionMap(
                self.functions[i].instructions.instruction)

        # Fill the list of registers that weren't modified in the function
        for i in range(len(self.functions)):
            for j in range(len(self.functions[i].registers_used)):
                i_reg = self.functions[i].registers_used[j]
                if i_reg in self.functions[i].registers_modified:
                    continue
                else:
                    self.functions[i].registers_unmodified.append(i_reg)

        # 5. Get a list of registers that are different from start and end along with their different values
        for i in range(len(self.functions)):
            for j in range(len(self.functions[i].initial_register_values)):
                reg = self.functions[i].initial_register_values[j][0]
                initial_value = self.functions[i].initial_register_values[j][1]
                final_value = self.functions[i].final_register_values[j][1]
                if initial_value != final_value:
                    self.functions[i].registers_different_values.append([reg, initial_value, final_value])

    # This function gets the function names from the assembly file.
    # It also gets a list of sub-function(functions that are called from a parent function)
    def get_functions(self, i_asm):
        i_found_function = False
        for i in range(len(i_asm)):
            i_line = i_asm[i]
            if i_found_function:
                # This is an original instruction in assembly form. Look for "call" instruction to get sub_functions
                if i_line.startswith('\t'):
                    i_line_components = i_line.split("\t")
                    if "call" in i_line_components:
                        i_func.list_sub_functions.append(i_line_components[-1])
                # This is the block name for a particular function
                elif i_line.startswith('.'):
                    i_func.list_blocks_names.append(i_line.split(":")[0])
                # This is the end of a function
                else:
                    # This is the start of a new function
                    self.functions.append(i_func)

                    function = i_line.split(':')[0]
                    if "." not in function:
                        i_func = Function(i_line.split(':')[0])
                        i_found_function = True
                    else:
                        i_found_function = False

            else:
                if i_line.startswith('\t') or i_line.startswith('.'):
                    continue
                else:
                    i_func = Function(i_line.split(':')[0])
                    i_found_function = True

        # The append the last function to the self.functions list
        self.functions.append(i_func)

        # Remove any duplicate sub_functions
        for i in range(len(self.functions)):
            i_new_list = []
            for j in range(len(self.functions[i].list_sub_functions)):
                if not self.functions[i].list_sub_functions[j] in i_new_list:
                    i_new_list.append(self.functions[i].list_sub_functions[j])
            # Update the entire list
            self.functions[i].list_sub_functions = i_new_list

    # This function gets the starting and ending addresses of each function along with a list of
    # instructions that makes up a function.
    def get_instructions(self, i_util_functions):
        # TODO: It is possible that there are more than 1 possible return calls within each function (besides the one
        #       at the very end of instruction stream). Currently we aren't handling this case.
        #
        for i in range(len(self.functions)):
            for j in range(len(i_util_functions.f_names)):
                if self.functions[i].name == i_util_functions.f_names[j]:
                    self.functions[i].starting_address = i_util_functions.f_address[j]
                    self.functions[i].ending_address = i_util_functions.f_instructions[j].address[-1]
                    self.functions[i].instructions = i_util_functions.f_instructions[j]


''' End of class definitions'''
