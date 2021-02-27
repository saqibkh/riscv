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
import function_map
from os import path


def checkFileExists(i_filename):
    if not utils.checkFileExists(i_filename):
        print("file: " + i_filename + " doesn't exist.")
        raise Exception


def generate_binary_file_from_s(i_original_s_file, simlog):
    # Make sure this is a ".s" file
    if not i_original_s_file.endswith('.s'):
        simlog.error("Error: Must provide a .s file.")
        raise Exception

    i_original_objdump_file = i_original_s_file.rsplit('.s', 1)[0] + ".objdump"
    i_original_executable = i_original_s_file.rsplit('.s', 1)[0]
    i_new_binary_s_file = i_original_s_file.rsplit('.s', 1)[0] + "_binary.s"
    i_new_binary_s_file_contents = []

    # Make sure the .s file, .objdump and executable files exist within the same directory
    checkFileExists(i_original_s_file)
    checkFileExists(i_original_objdump_file)
    checkFileExists(i_original_executable)

    map = utils.ControlFlowMapRevised(utils.readfile(i_original_s_file), utils.readfile(i_original_objdump_file),
                                      enable_functionMap=True, C_executable_File=i_original_executable,
                                      simlog=simlog)

    # i_inst_list_objdump = []
    # # Get a list of all instructions in order and their corresponding opcodes
    # for i in range(len(map.function_map.functions)):
    #     i_func = map.function_map.functions[0]
    #     i_num_instructions = len(i_func.instructions.instruction)
    #     i_num_opcodes = len(i_func.instructions.opcode)
    #     if i_num_instructions != i_num_opcodes:
    #         simlog.error("Opcodes and instruction numbers aren't same")
    #         raise Exception
    #     for j in range(len(i_func.instructions.instruction)):
    #         i_inst_list_objdump.append([i_func.instructions.instruction[j], i_func.instructions.opcode[j]])
    # del i_func, i_num_instructions, i_num_opcodes, i, j
    #
    # # Get a list of all instructions from the asm file
    # i_inst_list_asm = []
    # i_original_s_file_contents = utils.readfile(i_original_s_file)
    # for i in range(len(i_original_s_file_contents)):
    #     i_line = i_original_s_file_contents[i]
    #     if utils.is_instruction_asm(i_line):
    #         i_inst_list_asm.append(i_line.strip())

    i_function = 0
    i_original_s_file_contents = utils.readfile(i_original_s_file)
    for i in range(len(i_original_s_file_contents)):
        i_func_name = map.function_map.functions[i_function].name
        i_line = i_original_s_file_contents[i]

        if i_line == (i_func_name + ":"):
            i_new_binary_s_file_contents.append(i_line)
            for j in range(len(map.function_map.functions[i_function].instructions.opcode)):
                i_instruction = map.function_map.functions[i_function].instructions.instruction[j]
                i_opcode = map.function_map.functions[i_function].instructions.opcode[j]
                i_len_opcode = len(i_opcode)
                if i_len_opcode == 4:
                    i_new_binary_s_file_contents.append('\t.short(0x' + i_opcode + ")\t#" + i_instruction)
                elif i_len_opcode == 8:
                    i_new_binary_s_file_contents.append('\t.long(0x' + i_opcode + ")\t#" + i_instruction)
                else:
                    simlog.error("Length of opcode is not valid")
                    raise Exception

            if i_function < len(map.function_map.functions) - 1:
                i_function += 1

        # If it is a valid instruction then don't add to the list as it will be replaced by the opcodes
        elif utils.is_instruction_asm(i_line):
            continue

        # Copy all other statements from the asm file
        else:
            i_new_binary_s_file_contents.append(i_line)

    # Now the the contents to the new binary .s file
    with open(i_new_binary_s_file, 'w') as filehandle:
        for listitem in i_new_binary_s_file_contents:
            filehandle.write('%s\n' % listitem)
    return i_new_binary_s_file
