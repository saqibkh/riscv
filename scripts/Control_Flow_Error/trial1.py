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

# This new implementation is loosely based on CFCSS technique where we will assign a unique random compile time
# signature to each basic block. The run-time variable will be updated by each instruction (except instructions
# that have r10/r11 in the operand field). The instruction will be XOR'ed with the value originally held in r11.
# This run-time variable will be set at the start of each block to make sure no CFE has taken place.

class TRIAL1:
    def __init__(self, i_map):
        self.original_map = i_map

        # Compile time signatures are the XOR'ed values of each instruction in the basic block.
        # For the XOR'ed values, we will only consider the last 12 bits or 3-bytes
        self.compile_time_sig = []
        self.generate_compile_time_sig()

        # Generate D (run-time adjusting signature). When a basic block has multiple incoming edges,
        # the signature uses an extra variable D. This variable is updated by the predecessor basic blocks
        # and ensures that the run-time signature can be updated to the correct value,
        # regardless of which predecessor has executed.
        self.extended_signature = [None] * len(i_map.blocks)
        self.generate_extended_signature()

        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm

        utils.generate_instruction_mapping(self)

        # Generate the new assembly file
        self.generate_TRIAL1_file_updated()

        print("Finished processing TRIAL1")

    ''' Beginning of class function definitions '''
    def generate_TRIAL1_file_updated(self):
        i_block = 0
        i_line_num_new_asm_file = 0

        # 1. Loop the asm file lines until the end of file
        while i_line_num_new_asm_file < len(self.new_asm_file):
            # Return once all the blocks are processed
            if i_block == len(self.original_map.blocks):
                return

            block_found = False
            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file]

            # A basic block will start when the line matches the first line of that particular block
            if i_line_asm.startswith('\t'):
                i_line_asm = i_line_asm.split('\t', 1)[1]
                if not i_line_asm.startswith('.'):
                    i_line_block_obj = self.original_map.blocks[i_block].entries[0]
                    i_line_block_asm = utils.get_matching_asm_line_using_objdump_line(self.instruction_map,
                                                                                      i_line_block_obj)
                    try:
                        i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file].split('\t', 1)[1]
                        for i in range(len(i_line_block_asm)):
                            if self.original_map.file_asm[i_line_num_new_asm_file].split('\t', 1)[1] in \
                                    i_line_block_asm[i]:
                                block_found = True

                                del i_line_block_obj, i_line_block_asm, i_line_asm
                                break
                    except Exception as e:
                        # unexpected line encountered
                        i_line_num_new_asm_file += 1
                        continue

            if block_found:
                # For initial basic block we need to load 0 into r11
                i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file] # delete me after use
                if len(self.original_map.blocks[i_block].previous_block_id) == 0:
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts11,0')
                    i_line_num_new_asm_file += 1

                # Need to check the run-time signature
                else:
                    # Update the run_time signature with any possible extended signature
                    if len(self.original_map.blocks[i_block].previous_block_id) > 1:
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    # Check the run_time signature now
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txori\ts11,s11,' +
                                             str(int(self.compile_time_sig[self.original_map.blocks[i_block].previous_block_id[0]],16)))
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tbnez\ts11,'+utils.exception_handler_address)
                    i_line_num_new_asm_file += 1

                # Add the XOR instruction before each real instruction. This is important because we
                # can't add XOR instruction after the branch/jump instruction.
                for i in range(len(self.original_map.blocks[i_block].entries)):
                    i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file]
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txori\ts11,s11,' + str(int(self.original_map.blocks[i_block].opcode[i][-2:], 16)))
                    i_line_num_new_asm_file += 2

                # We need to update the extended signature variable at the end of each block
                i_line_num_new_asm_file -= 1
                if self.extended_signature[i_block] != None:
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + self.extended_signature[i_block])
                else:
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,0')
                i_line_num_new_asm_file += 2

                # Finish processing the block
                i_block += 1
                i_line_num_new_asm_file -= 1


            i_line_num_new_asm_file += 1

    def generate_extended_signature(self):
        for i in range(len(self.original_map.blocks)):
            if len(self.original_map.blocks[i].previous_block_id) > 1:
                # Get the signature of the first incoming block
                i_predecessor_block_0 = self.original_map.blocks[i].previous_block_id[0]
                D_sign = self.compile_time_sig[i_predecessor_block_0]
                for j in range(len(self.original_map.blocks[i].previous_block_id) - 1):
                    predesessor_block_id_next = self.original_map.blocks[i].previous_block_id[j + 1]
                    D_sign = hex(int(D_sign,16) ^ int(self.compile_time_sig[predesessor_block_id_next],16))
                    # Get the ID of the incoming blocks
                    incoming_block_id = self.original_map.blocks[i].previous_block_id[j + 1]
                    self.extended_signature[incoming_block_id] = D_sign

    def generate_compile_time_sig(self):

        for i in range(len(self.original_map.blocks)):
            cum_sig = 0

            for j in range(len(self.original_map.blocks[i].opcode)):
                i_inst_opcode = self.original_map.blocks[i].opcode[j]
                # Each instruction has to be greater than 4-bytes (16-bits)
                if(len(i_inst_opcode) < 4):
                    print("For some reason the instruction is less than 4 bytes")
                    raise Exception
                # XOR'ed with the existing value.
                cum_sig ^= int(i_inst_opcode, 16)

            # Add the XOR'ed value of each instruction within the basic block to the compile_time sig variable.
            # Note: Only consider the last 2-bytes for now as Load Immediate takes only 12-bits of immediate value
            self.compile_time_sig.append('0x' + hex(cum_sig)[-2:])

    ''' End of class function definitions '''
